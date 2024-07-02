from unittest import mock

mock.patch("osprey.server.lib.globus_search.DSaaSSearchClient")
mock.patch("osprey.server.jobs.timer.set_timer", return_value=1111)
mock.patch("osprey.server.jobs.user_flow.run_flow")
