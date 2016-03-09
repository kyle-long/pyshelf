import pyproctor
from moto import mock_s3
from pyshelf.app import app
import pyshelf.configure as configure
import boto
from boto.s3.key import Key
import yaml
import metadata_utils as meta_utils
import permission_utils as utils
from route_tester.tester import Tester


class FunctionalTestBase(pyproctor.TestBase):
    RESPONSE_404 = {
        "message": "Resource not found",
        "code": "resource_not_found"
    }

    def setUp(self):
        self.app = app
        self.configure_moto()
        self.test_client = app.test_client()
        self._route_tester = None

    @classmethod
    def setUpClass(cls):
        config = {
            "accessKey": "test",
            "secretKey": "test",
            "bucketName": "test"
        }
        configure.logger(app.logger, "DEBUG")
        app.config.update(config)

    def configure_moto(self):
        self.moto_s3 = mock_s3()
        self.moto_s3.start()
        self.boto_connection = boto.connect_s3()
        self.boto_connection.create_bucket("test")
        self.test_bucket = self.boto_connection.get_bucket("test")
        self.configure_artifacts()
        self.create_auth_key()

    def configure_artifacts(self):
        key = Key(self.test_bucket, "test")
        key.set_contents_from_string("hello world")
        nested_key = Key(self.test_bucket, "/dir/dir2/dir3/nest-test")
        nested_key.set_contents_from_string("hello world")
        # Metadata for artifacts
        meta_key = Key(self.test_bucket, "_metadata_test.yaml")
        meta_key.set_contents_from_string(yaml.dump(meta_utils.get_meta()))
        nest_meta_key = Key(self.test_bucket, "/dir/dir2/dir3/_metadata_nest-test.yaml")
        nest_meta_key.set_contents_from_string("")
        Key(self.test_bucket, "/dir/dir2/dir3/dir4/")
        artifact_list = Key(self.test_bucket, "/dir/dir2/dir3/dir4/test5")
        artifact_list.set_contents_from_string("")

    def create_auth_key(self):
        self.auth = utils.auth_header()
        key_name = "_keys/{}".format(self.auth["Authorization"])
        auth_key = Key(self.test_bucket, key_name)
        auth_key.set_contents_from_string(utils.get_permissions_func_test())

    @property
    def route_tester(self):
        if not self._route_tester:
            self._route_tester = Tester(self, self.test_client)

        return self._route_tester

    def tearDown(self):
        self.moto_s3.stop()

    def response_500(self, message=None):
        if not message:
            message = "Internal server error"

        return {
            "message": message,
            "code": "internal_server"
        }