import json
import re
from decimal import Decimal

import pytest
import responses
from monerorpc.authproxy import (
    AuthServiceProxy,
    EncodeDecimal,
    JSONRPCException,
)


class TestEncodeDecimal:
    def test_encodes_ok(self):
        assert json.dumps(Decimal(2), default=EncodeDecimal)

    def test_encoding_fail(self):
        with pytest.raises(TypeError):
            json.dumps(self, default=EncodeDecimal)


class TestAuthServiceProxy:
    dummy_url = "http://dummy-rpc:8000/json_rpc"

    @responses.activate
    def test_good_call(self):
        responses.add(responses.POST, self.dummy_url, json={"result": "dummy"})
        client = AuthServiceProxy(self.dummy_url)
        resp = client.status()
        assert resp == "dummy"

    @responses.activate
    @pytest.mark.parametrize("code", (500, 404))
    def test_http_error_raises_error(self, code):
        responses.add(responses.POST, self.dummy_url, status=code)
        client = AuthServiceProxy(self.dummy_url)
        with pytest.raises(JSONRPCException):
            client.dummy_method()

    @responses.activate
    def test_empty_response_raises_error(self):
        responses.add(responses.POST, self.dummy_url, status=200, json={})
        client = AuthServiceProxy(self.dummy_url)
        with pytest.raises(JSONRPCException):
            client.dummy_method()

    @responses.activate
    def test_rpc_error_raises_error(self):
        responses.add(
            responses.POST,
            self.dummy_url,
            status=200,
            json={"error": "dummy error"},
        )
        client = AuthServiceProxy(self.dummy_url)
        with pytest.raises(JSONRPCException):
            client.dummy_method()

    @responses.activate
    def test_calls_batch(self):
        for n in range(2):
            responses.add(
                responses.POST,
                self.dummy_url,
                status=200,
                json={"result": f"dummy - {n}"},
            )
        client = AuthServiceProxy(self.dummy_url)
        cases = [["dummy_method_1", {}], ["dummy_method_2", "dummy"]]
        results = client.batch_(cases)
        assert len(results) == len(cases)
