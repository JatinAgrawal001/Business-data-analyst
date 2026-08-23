from app.storage.supabase import storage_service
from app.utils.sanitization import sanitize_path_component, generate_secure_filename

def test_storage_path_sanitization():
    """
    Test path sanitization strips traversal and control characters
    """
    traversal_input = "../../secrets/..//evil"
    cleaned = sanitize_path_component(traversal_input)
    assert ".." not in cleaned
    assert "/" not in cleaned
    assert "\\" not in cleaned

def test_secure_filename_generation():
    """
    Test secure filename generation has timestamp and entropy
    """
    original = "My Sales Report 2026.csv"
    generated = generate_secure_filename(original)
    assert generated.endswith(".csv")
    assert "sales" in generated.lower()
    assert len(generated.split("_")) >= 3

def test_storage_service_path_builder():
    """
    Test storage service generates user & project isolated path
    """
    user_id = "user-123"
    project_id = "proj-456"
    path_info = storage_service.build_storage_path(
        user_id=user_id,
        project_id=project_id,
        original_filename="dataset.csv"
    )
    assert path_info["bucket"] == "datasets"
    assert path_info["path"].startswith("user-123/proj-456/")
    assert path_info["path"].endswith(".csv")
