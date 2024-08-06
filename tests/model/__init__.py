from unittest import mock

mock.patch("aero.lib.globus_search.DSaaSSearchClient")
mock.patch("aero.jobs.timer.set_timer", return_value=1111)
mock.patch("aero.jobs.user_flow.run_flow")
