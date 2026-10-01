from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "personal-finance-intelligence"


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "test.txt",
                b"this is not a supported file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Only CSV and PDF files are supported."
    )


def test_upload_rejects_file_over_10_mb():
    oversized_content = b"x" * (10 * 1024 * 1024 + 1)

    response = client.post(
        "/api/upload",
        files={
            "file": (
                "oversized.csv",
                oversized_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413

    assert response.json()["detail"] == (
        "File is too large. Maximum allowed size is 10 MB."
    )


def test_upload_hides_malformed_file_details():
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "malformed.csv",
                (
                    b"Date,Description,Debit,Credit,Balance\n"
                    b"2026-09-30,TEST MERCHANT,"
                    b"not-a-number,,10000\n"
                ),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "The uploaded file contains invalid or "
        "unsupported transaction data."
    )


def test_analyze_hides_malformed_file_details():
    response = client.post(
        "/api/analyze",
        files={
            "file": (
                "malformed.csv",
                (
                    b"Date,Description,Debit,Credit,Balance\n"
                    b"2026-09-30,TEST MERCHANT,"
                    b"not-a-number,,10000\n"
                ),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "The uploaded file contains invalid or "
        "unsupported transaction data."
    )


def test_concurrent_uploads_are_isolated():
    csv_a = (
        b"Date,Description,Debit,Credit,Balance\n"
        b"2026-09-01,SWIGGY ORDER,500,,9500\n"
    )

    csv_b = (
        b"Date,Description,Debit,Credit,Balance\n"
        b"2026-09-01,AMAZON ORDER,1200,,8800\n"
    )

    def upload(filename, content):
        return client.post(
            "/api/upload",
            files={
                "file": (
                    filename,
                    content,
                    "text/csv",
                )
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            upload,
            "user_a.csv",
            csv_a,
        )

        future_b = executor.submit(
            upload,
            "user_b.csv",
            csv_b,
        )

        response_a = future_a.result()
        response_b = future_b.result()

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    data_a = response_a.json()
    data_b = response_b.json()

    assert data_a["filename"] == "user_a.csv"
    assert data_b["filename"] == "user_b.csv"

    assert data_a["transaction_count"] == 1
    assert data_b["transaction_count"] == 1

    assert data_a["transactions"][0]["description"] == (
        "SWIGGY ORDER"
    )

    assert data_b["transactions"][0]["description"] == (
        "AMAZON ORDER"
    )


def test_upload_cleans_up_temp_file_on_processing_failure(monkeypatch):
    import tempfile
    from pathlib import Path

    created_paths = []

    original_named_temporary_file = tempfile.NamedTemporaryFile

    def tracking_named_temporary_file(*args, **kwargs):
        temp_file = original_named_temporary_file(
            *args,
            **kwargs,
        )
        created_paths.append(temp_file.name)
        return temp_file

    def fail_processing(file_path, file_extension):
        raise RuntimeError("simulated processing failure")

    monkeypatch.setattr(
        "backend.main.NamedTemporaryFile",
        tracking_named_temporary_file,
    )

    monkeypatch.setattr(
        "backend.main.process_uploaded_file",
        fail_processing,
    )

    response = client.post(
        "/api/upload",
        files={
            "file": (
                "failure.csv",
                (
                    b"Date,Description,Debit,Credit,Balance\n"
                    b"2026-09-30,TEST MERCHANT,100,,10000\n"
                ),
                "text/csv",
            )
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to process file."

    assert len(created_paths) == 1
    assert not Path(created_paths[0]).exists()