from agx.config import HOME, format_workspace_uri


def test_format_workspace_uri():
    # Base HOME directory URI
    home_uri = f"file://{HOME}"
    assert format_workspace_uri(home_uri) == "~"

    # Subdirectory in HOME
    sub_uri = f"file://{HOME}/projects/myrepo"
    assert format_workspace_uri(sub_uri) == "~/projects/myrepo"

    # Non-home URI
    other_uri = "file:///var/data/project"
    assert format_workspace_uri(other_uri) == "/var/data/project"

    # Empty string
    assert format_workspace_uri("") == ""
