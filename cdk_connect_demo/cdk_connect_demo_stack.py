import aws_cdk
from aws_cdk import (
    # Duration,
    Stack,
    aws_sqs as sqs,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_iam as iam,
    Aws,
    CfnOutput
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct


class CdkConnectDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "CdkConnectDemoQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        # prd_log_group = logs.LogGroup(self, "connect-demo-apigw-log")
        api = apigw.RestApi(self,
                            "connect-demo",
                            endpoint_configuration=apigw.EndpointConfiguration(types=[apigw.EndpointType.REGIONAL]),
                            deploy_options=apigw.StageOptions(
                                stage_name="live",
                                logging_level=apigw.MethodLoggingLevel.INFO,
                                data_trace_enabled=True
                            )
                            )
        sqs_send_message = api.root.add_resource("sqs").add_resource("send_message")
        lambda_invoke = api.root.add_resource("lambda").add_resource("invoke")

        # TBD Create a SQS queue

        queue_name = "connect-demo-queue"
        connect_demo_queue = sqs.Queue(self,
                                       "ConnectDemoQueue",
                                       queue_name=queue_name,
                                       visibility_timeout=aws_cdk.Duration.minutes(1)
                                       )

        role_name = "Connect-Demo-ApigwRole"
        apigw_role = iam.Role(self, "ApigwRole",
                              role_name=role_name,
                              assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
                              description="Role for api gateway"
                              )
        apigw_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess"))

        aws_region = Aws.REGION
        path_override = Aws.ACCOUNT_ID + "/" + queue_name
        # path_override=path_override.format(queue_name)

        integration_option = apigw.IntegrationOptions(
            passthrough_behavior=apigw.PassthroughBehavior.NEVER,
            request_templates={
                "application/json": "Action=SendMessage&MessageBody=$input.body"
            },
            request_parameters={
                "integration.request.header.Content-Type": "\'application/x-www-form-urlencoded\'"
            },
            credentials_role=apigw_role,
            integration_responses=[{
                "statusCode": "200"
            }]

        )

        sqs_send_message_integration = apigw.AwsIntegration(
            service="sqs",
            path=path_override,
            region=aws_region,
            integration_http_method="POST",
            options=integration_option
        )

        sqs_send_message.add_method("POST",
                                    sqs_send_message_integration,
                                    authorization_type=apigw.AuthorizationType.NONE,
                                    method_responses=[{
                                        "statusCode": "200",
                                    }]
                                    )

        lambda_role_name = "Connect-Demo-LambdaRole"
        lambda_role = iam.Role(self, "LambdaRole",
                               role_name=lambda_role_name,
                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                               description="Role for lambda"
                               )
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambdaExecute"))

        lambda_backend = _lambda.Function(
            self, 'BackendLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda'),
            handler='backend.handler',
            role=iam.Role.from_role_arn(self, 'execution_role', lambda_role.role_arn),
            timeout=aws_cdk.Duration.seconds(10)
        )

        lambda_invoke_integration = apigw.LambdaIntegration(lambda_backend)

        lambda_invoke.add_method("POST",
                                 lambda_invoke_integration,
                                 authorization_type=apigw.AuthorizationType.NONE,
                                 )

        sqs_lambda_backend = _lambda.Function(
            self, 'SQSLambdaBackendLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda'),
            handler='sqs_lambda_backend.handler',
            role=iam.Role.from_role_arn(self, 'SqsLambdaExecutionRole', lambda_role.role_arn),
            timeout=aws_cdk.Duration.seconds(10)
        )

        event_source = SqsEventSource(connect_demo_queue, batch_size=100, max_batching_window=aws_cdk.Duration.seconds(1))
        sqs_lambda_backend.add_event_source(event_source)
        event_source_id = event_source.event_source_mapping_id
        # print(event_source_id)

        deployment = apigw.Deployment(self, "Deployment", api=api)
        # print(connect_demo_queue.queue_name)
        # print(api.url)

        CfnOutput(self, "UrlDirectInvoke", value=api.deployment_stage.url_for_path(path='/lambda/invoke'))
        CfnOutput(self, "UrlSQSSendMessage", value=api.deployment_stage.url_for_path(path='/sqs/send_message'))
        CfnOutput(self, "BackendLambdaArn", value=lambda_backend.function_arn)
        CfnOutput(self, "SQSLambdaBackendLambdaArn", value=sqs_lambda_backend.function_arn)
        CfnOutput(self, "ConnectDemoQueueArn", value=connect_demo_queue.queue_arn)
