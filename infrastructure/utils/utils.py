from aws_cdk import (
    aws_rds as rds
)

rds_capacity_units = {1: rds.AuroraCapacityUnit.ACU_1, 2: rds.AuroraCapacityUnit.ACU_2, 4: rds.AuroraCapacityUnit.ACU_4,
                      8: rds.AuroraCapacityUnit.ACU_8, 16: rds.AuroraCapacityUnit.ACU_16,
                      32: rds.AuroraCapacityUnit.ACU_32, 64: rds.AuroraCapacityUnit.ACU_64,
                      128: rds.AuroraCapacityUnit.ACU_128, 192: rds.AuroraCapacityUnit.ACU_192,
                      256: rds.AuroraCapacityUnit.ACU_256, 384: rds.AuroraCapacityUnit.ACU_384}
