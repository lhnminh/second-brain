def test_dashboard_page_and_api_share_an_origin(setup):
    clients, _, _ = setup
    client = clients()
    page = client.get("/")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert page.headers["cache-control"] == "no-store"
    assert 'id="task-form"' in page.text
    assert 'id="reviews"' in page.text
    assert "fetch(path" in page.text
    assert client.get("/api/dashboard").status_code == 200


def test_page_does_not_embed_server_secrets(setup):
    clients, _, _ = setup
    client = clients(token="secret-demo-token")
    page = client.get("/")
    assert page.status_code == 200
    assert "secret-demo-token" not in page.text
    assert client.get("/api/dashboard").status_code == 401


def test_dashboard_resource_when_backend_package_is_installed_elsewhere(
    setup, monkeypatch, tmp_path
):
    import second_brain.api as api_module

    clients, _, _ = setup
    monkeypatch.setattr(
        api_module,
        "__file__",
        str(tmp_path / "site-packages" / "second_brain" / "api.py"),
    )
    page = clients().get("/")
    assert page.status_code == 200
    assert 'id="task-form"' in page.text
