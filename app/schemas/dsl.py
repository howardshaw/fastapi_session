from typing import Dict, List, Any

from pydantic import BaseModel, Field


class ActivityDefinition(BaseModel):
    name: str
    arguments: List[str]
    result: str


class Activity(BaseModel):
    activity: ActivityDefinition


class SequenceDefinition(BaseModel):
    elements: List[Dict[str, Any]]


class Sequence(BaseModel):
    sequence: SequenceDefinition


class ParallelBranches(BaseModel):
    branches: List[Sequence]


class Parallel(BaseModel):
    parallel: ParallelBranches


class RootDefinition(BaseModel):
    sequence: SequenceDefinition


class DSLRequest(BaseModel):
    """工作流 DSL 请求"""
    variables: Dict[str, str] = Field(
        default_factory=dict,
        description="工作流变量定义",
        examples=[{"arg1": "value1", "arg2": "value2"}]
    )
    root: RootDefinition = Field(
        ...,
        description="工作流根节点定义",
        examples=[{
            "sequence": {
                "elements": [
                    {
                        "activity": {
                            "name": "activity1",
                            "arguments": ["arg1"],
                            "result": "result1"
                        }
                    },
                    {
                        "activity": {
                            "name": "activity2",
                            "arguments": ["result1"],
                            "result": "result2"
                        }
                    },
                    {
                        "activity": {
                            "name": "activity3",
                            "arguments": ["arg2", "result2"],
                            "result": "result3"
                        }
                    }
                ]
            }
        }]
    )

    def to_dsl_input(self) -> "DSLInput":
        """将 DSLRequest 转换为 DSLInput"""
        from app.workflows.dsl.workflows import DSLInput, ActivityStatement, ActivityInvocation, \
            SequenceStatement, Sequence, ParallelStatement, Parallel

        def convert_activity(act_def: Dict[str, Any]) -> ActivityStatement:
            return ActivityStatement(
                activity=ActivityInvocation(
                    name=act_def["name"],
                    arguments=act_def["arguments"],
                    result=act_def["result"]
                )
            )

        def convert_sequence(seq_def: Dict[str, Any]) -> SequenceStatement:
            elements = []
            for elem in seq_def["elements"]:
                if "activity" in elem:
                    elements.append(convert_activity(elem["activity"]))
                elif "parallel" in elem:
                    elements.append(convert_parallel(elem["parallel"]))
            return SequenceStatement(sequence=Sequence(elements=elements))

        def convert_parallel(par_def: Dict[str, Any]) -> ParallelStatement:
            branches = []
            for branch in par_def["branches"]:
                if "sequence" in branch:
                    branches.append(convert_sequence(branch["sequence"]))
            return ParallelStatement(parallel=Parallel(branches=branches))

        # 转换根节点
        root_statement = convert_sequence(self.root.sequence.dict())

        return DSLInput(
            root=root_statement,
            variables=self.variables
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "variables": {
                    "arg1": "value1",
                    "arg2": "value2"
                },
                "root": {
                    "sequence": {
                        "elements": [
                            {
                                "activity": {
                                    "name": "activity1",
                                    "arguments": ["arg1"],
                                    "result": "result1"
                                }
                            },
                            {
                                "activity": {
                                    "name": "activity2",
                                    "arguments": ["result1"],
                                    "result": "result2"
                                }
                            },
                            {
                                "activity": {
                                    "name": "activity3",
                                    "arguments": ["arg2", "result2"],
                                    "result": "result3"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }


# 需要在类定义后更新 Forward References
SequenceDefinition.model_rebuild()
