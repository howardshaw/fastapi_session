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
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="工作流变量定义",
        examples=[{
            "resource_id": "0194434a-70cc-78d0-b960-1157ce9c02d3",
            "collection_name": "dataset",
            "faq_collection_name": "dataset_faq",
            "summary_collection_name": "dataset_summary",
            "clean_transform": "clean",
            "hypothetical_question_transform": "hypothetical_question",
            "summary_transform": "summary",
            "chunk_size": 512,
        }]
    )
    root: RootDefinition = Field(
        ...,
        description="工作流根节点定义",
        examples=[{
            "sequence": {
                "elements": [
                    {
                        "activity": {
                            "name": "load_document",
                            "arguments": [
                                "resource_id"
                            ],
                            "result": "documents"
                        }
                    },
                    {
                        "activity": {
                            "name": "transform_documents",
                            "arguments": [
                                "documents",
                                "clean_transform"
                            ],
                            "result": "cleaned_documents"
                        }
                    },
                    {
                        "activity": {
                            "name": "split_documents",
                            "arguments": [
                                "cleaned_documents",
                                "chunk_size"
                            ],
                            "result": "splits"
                        }
                    },
                    {
                        "parallel": {
                            "branches": [
                                {
                                    "sequence": {
                                        "elements": [
                                            {
                                                "activity": {
                                                    "name": "store_documents",
                                                    "arguments": ["splits"],
                                                    "result": "docstore"
                                                }
                                            },
                                            {
                                                "parallel": {
                                                    "branches": [
                                                        {
                                                            "sequence": {
                                                                "elements": [
                                                                    {
                                                                        "activity": {
                                                                            "name": "transform_documents",
                                                                            "arguments": [
                                                                                "splits",
                                                                                "hypothetical_question_transform"
                                                                            ],
                                                                            "result": "questions"
                                                                        }
                                                                    },
                                                                    {
                                                                        "activity": {
                                                                            "name": "store_vectors",
                                                                            "arguments": [
                                                                                "questions",
                                                                                "faq_collection_name"
                                                                            ],
                                                                            "result": "questions_result"
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        },
                                                        {
                                                            "sequence": {
                                                                "elements": [
                                                                    {
                                                                        "activity": {
                                                                            "name": "transform_documents",
                                                                            "arguments": [
                                                                                "splits",
                                                                                "summary_transform"
                                                                            ],
                                                                            "result": "summary"
                                                                        }
                                                                    },
                                                                    {
                                                                        "activity": {
                                                                            "name": "store_vectors",
                                                                            "arguments": [
                                                                                "summary",
                                                                                "summary_collection_name"
                                                                            ],
                                                                            "result": "summary_result"
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "activity": {
                                        "name": "store_vectors",
                                        "arguments": [
                                            "splits",
                                            "collection_name"
                                        ],
                                        "result": "vectors_result"
                                    }
                                }
                            ]
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
                    result=act_def.get("result", ""),
                )
            )

        def convert_sequence(seq_def: Dict[str, Any]) -> SequenceStatement:
            elements = []
            for elem in seq_def["elements"]:
                if "activity" in elem:
                    elements.append(convert_activity(elem["activity"]))
                elif "parallel" in elem:
                    elements.append(convert_parallel(elem["parallel"]))
                elif "sequence" in elem:
                    elements.append(convert_sequence(elem["sequence"]))
            return SequenceStatement(sequence=Sequence(elements=elements))

        def convert_parallel(par_def: Dict[str, Any]) -> ParallelStatement:
            branches = []
            for branch in par_def["branches"]:
                if "sequence" in branch:
                    branches.append(convert_sequence(branch["sequence"]))
                elif "activity" in branch:
                    branches.append(convert_activity(branch["activity"]))
                elif "parallel" in branch:
                    branches.append(convert_parallel(branch["parallel"]))

            return ParallelStatement(parallel=Parallel(branches=branches))

        # 转换根节点
        root_statement = convert_sequence(self.root.sequence.dict())

        return DSLInput(
            root=root_statement,
            variables=self.variables
        )
