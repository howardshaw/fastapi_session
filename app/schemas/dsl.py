from typing import Dict, List, Optional, Union, Any, Annotated
from fastapi import Body
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
    variables: Dict[str, str] = Field(default_factory=dict, description="工作流变量定义")
    root: RootDefinition = Field(..., description="工作流根节点定义")

    class Config:
        schema_extra = {
            "examples": [{
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
            }]
        }


# 需要在类定义后更新 Forward References
SequenceDefinition.model_rebuild()
