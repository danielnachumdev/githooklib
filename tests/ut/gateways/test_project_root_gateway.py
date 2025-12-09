import unittest

from githooklib.gateways.project_root_gateway import ProjectRootGateway
from tests.base_test_case import BaseTestCase


class TestProjectRootGateway(BaseTestCase):
    def test_find_project_root_returns_path_ending_with_githooklib(self):
        result = ProjectRootGateway.find_project_root()
        result = self.unwrap_optional(result)
        self.assertEqual("githooklib", result.name)


if __name__ == "__main__":
    unittest.main()
