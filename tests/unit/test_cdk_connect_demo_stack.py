import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_connect_demo.cdk_connect_demo_stack import CdkConnectDemoStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_connect_demo/cdk_connect_demo_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkConnectDemoStack(app, "cdk-connect-demo")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
