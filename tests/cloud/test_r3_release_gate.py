"""Public download metadata cannot turn truthy strings into launch approval."""
import pytest
from fastapi.testclient import TestClient
from cloud.config import Settings
from cloud.main import create_app


@pytest.fixture
def release_client(tmp_path):
    settings=Settings(database_url='sqlite:///'+str(tmp_path/'release.sqlite'),
        session_secret='release-test-secret-not-a-production-credential',environment='test')
    settings.release={'version':'fixture-only','verified':True,'public_distribution_authorized':True,
        'signing_verified':True,'clean_windows_verified':True,'license_clearance':'CLEARED',
        'sha256':'a'*64,'url':'https://downloads.example.invalid/KStudio-fixture.exe'}
    app=create_app(settings)
    with TestClient(app) as client:
        yield settings,client
    app.state.engine.dispose()


@pytest.mark.parametrize('key,value',[
    ('verified','true'),('verified','false'),('verified',1),('verified',False),
    ('public_distribution_authorized','true'),('public_distribution_authorized',1),
    ('public_distribution_authorized',False),('sha256','a'*63),('sha256','x'*64),
    ('sha256',None),('url','http://downloads.example.invalid/setup.exe'),
    ('url','https://user:secret@downloads.example.invalid/setup.exe'),
    ('url','https://downloads.example.invalid/setup.exe#fragment'),('url','file:///C:/setup.exe'),
    ('url','https:///setup.exe'),('signing_verified',False),('signing_verified','true'),
    ('clean_windows_verified',False),('clean_windows_verified',1),('license_clearance','REVIEW_REQUIRED'),('license_clearance',True)])
def test_invalid_or_truthy_release_fields_keep_download_closed(release_client,key,value):
    settings,client=release_client;settings.release[key]=value
    result=client.get('/api/public/config')
    assert result.status_code==200
    release=result.json()['release']
    assert release['download_available'] is False and release['url'] is None


def test_download_switch_overrides_valid_operator_release_metadata(release_client):
    settings,client=release_client;settings.download_enabled=False
    release=client.get('/api/public/config').json()['release']
    assert release['download_available'] is False and release['url'] is None


def test_public_release_exposes_only_website_fields(release_client):
    settings, client = release_client
    settings.release['private_manifest_file'] = 'private-release-manifest.json'
    settings.release['compatibility'] = [{'name':'SketchUp 2024', 'status':'BETA', 'internal_note':'private'}]
    release = client.get('/api/public/config').json()['release']
    assert 'private_manifest_file' not in release
    assert release['compatibility'] == [{'name':'SketchUp 2024','status':'BETA'}]


def test_valid_explicit_release_metadata_is_not_a_real_download_acceptance(release_client):
    _,client=release_client
    release=client.get('/api/public/config').json()['release']
    assert release['download_available'] is True
    assert release['url']=='https://downloads.example.invalid/KStudio-fixture.exe'
    # This is only an API gate test. No installer/network/Authenticode check is
    # fabricated by the fixture; real release approval is a separate operation.
