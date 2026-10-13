import json
import unittest

from app.handler import handler


class FakeContext:
    aws_request_id = "test-request-id"


def event(method="GET", query=""):
    return {"requestContext": {"http": {"method": method}}, "rawQueryString": query}


class HandlerTests(unittest.TestCase):
    def test_health_response(self):
        result = handler(event(), FakeContext())
        body = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["greeting"], "Hello, world!")

    def test_name_query(self):
        result = handler(event(query="name=Prudhvi"), FakeContext())
        self.assertEqual(json.loads(result["body"])["greeting"], "Hello, Prudhvi!")

    def test_empty_name_uses_default(self):
        result = handler(event(query="name=%20%20"), FakeContext())
        self.assertEqual(json.loads(result["body"])["greeting"], "Hello, world!")

    def test_rejects_long_name(self):
        result = handler(event(query="name=" + "x" * 81), FakeContext())
        self.assertEqual(result["statusCode"], 400)

    def test_rejects_non_get(self):
        self.assertEqual(handler(event(method="POST"), FakeContext())["statusCode"], 405)


if __name__ == "__main__":
    unittest.main()
