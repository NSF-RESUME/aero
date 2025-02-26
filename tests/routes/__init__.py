import sys
import tests.mock_globus

sys.modules["aero.globus.globus"] = tests.mock_globus
