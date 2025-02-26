from enum import IntEnum


class FlowEnum(IntEnum):
    VERIFY_AND_MODIFY = 0
    USER_FLOW = 1


# PERMANENT
FLOW_IDS = {
    FlowEnum.VERIFY_AND_MODIFY: "6f04c927-d319-41ae-a027-561329e4c2d1",
    FlowEnum.USER_FLOW: "0d8ace1a-d583-4f65-834e-4e1e1f450ecc",
}
