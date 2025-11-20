"""
JMeter Test Plan Generator
Generates JMeter .jmx file for 5000 req/min load testing
"""

import json
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def create_jmeter_test_plan():
    """
    Create JMeter test plan XML for face recognition load test
    Target: 5000 req/min for 10 minutes = 50000 total requests
    """
    
    # Root element
    jmeterTestPlan = Element('jmeterTestPlan', version="1.2", properties="5.0", jmeter="5.5")
    
    # Hash tree
    hashTree = SubElement(jmeterTestPlan, 'hashTree')
    
    # Test Plan
    testPlan = SubElement(hashTree, 'TestPlan', guiclass="TestPlanGui", testclass="TestPlan", testname="Face Recognition Load Test", enabled="true")
    
    # Test Plan properties
    SubElement(testPlan, 'stringProp', name="TestPlan.comments").text = "Load test for face recognition API - Target 5000 req/min"
    SubElement(testPlan, 'boolProp', name="TestPlan.functional_mode").text = "false"
    SubElement(testPlan, 'boolProp', name="TestPlan.tearDown_on_shutdown").text = "true"
    SubElement(testPlan, 'boolProp', name="TestPlan.serialize_threadgroups").text = "false"
    
    # Element properties
    elementProp = SubElement(testPlan, 'elementProp', name="TestPlan.user_defined_variables", elementType="Arguments", guiclass="ArgumentsPanel", testclass="Arguments", testname="User Defined Variables", enabled="true")
    collectionProp = SubElement(elementProp, 'collectionProp', name="Arguments.arguments")
    
    # Variables
    variables = [
        ("API_HOST", "${__P(api.host,your-api-gateway.amazonaws.com)}"),
        ("API_PORT", "${__P(api.port,443)}"),
        ("API_PROTOCOL", "${__P(api.protocol,https)}"),
        ("USERS", "${__P(users,100)}"),
        ("RAMP_UP", "${__P(rampup,60)}"),
        ("DURATION", "${__P(duration,600)}"),  # 10 minutes
    ]
    
    for name, value in variables:
        elementProp = SubElement(collectionProp, 'elementProp', name=name, elementType="Argument")
        SubElement(elementProp, 'stringProp', name="Argument.name").text = name
        SubElement(elementProp, 'stringProp', name="Argument.value").text = value
        SubElement(elementProp, 'stringProp', name="Argument.metadata").text = "="
    
    # Test Plan hash tree
    planHashTree = SubElement(hashTree, 'hashTree')
    
    # Thread Group
    threadGroup = SubElement(planHashTree, 'ThreadGroup', guiclass="ThreadGroupGui", testclass="ThreadGroup", testname="Face Recognition Users", enabled="true")
    SubElement(threadGroup, 'stringProp', name="ThreadGroup.on_sample_error").text = "continue"
    
    threadGroupProp = SubElement(threadGroup, 'elementProp', name="ThreadGroup.main_controller", elementType="LoopController", guiclass="LoopControlPanel", testclass="LoopController", testname="Loop Controller", enabled="true")
    SubElement(threadGroupProp, 'boolProp', name="LoopController.continue_forever").text = "false"
    SubElement(threadGroupProp, 'intProp', name="LoopController.loops").text = "-1"
    
    SubElement(threadGroup, 'stringProp', name="ThreadGroup.num_threads").text = "${USERS}"
    SubElement(threadGroup, 'stringProp', name="ThreadGroup.ramp_time").text = "${RAMP_UP}"
    SubElement(threadGroup, 'boolProp', name="ThreadGroup.scheduler").text = "true"
    SubElement(threadGroup, 'stringProp', name="ThreadGroup.duration").text = "${DURATION}"
    SubElement(threadGroup, 'stringProp', name="ThreadGroup.delay").text = "0"
    
    # Thread Group hash tree
    threadHashTree = SubElement(planHashTree, 'hashTree')
    
    # HTTP Header Manager
    headerManager = SubElement(threadHashTree, 'HeaderManager', guiclass="HeaderPanel", testclass="HeaderManager", testname="HTTP Header Manager", enabled="true")
    headerCollection = SubElement(headerManager, 'collectionProp', name="HeaderManager.headers")
    
    headers = [
        ("Content-Type", "application/json"),
        ("Accept", "application/json"),
        ("Authorization", "Bearer ${JWT_TOKEN}"),
    ]
    
    for name, value in headers:
        elementProp = SubElement(headerCollection, 'elementProp', name="", elementType="Header")
        SubElement(elementProp, 'stringProp', name="Header.name").text = name
        SubElement(elementProp, 'stringProp', name="Header.value").text = value
    
    SubElement(threadHashTree, 'hashTree')
    
    # Identify Request (90% weight)
    identifyRequest = SubElement(threadHashTree, 'HTTPSamplerProxy', guiclass="HttpTestSampleGui", testclass="HTTPSamplerProxy", testname="POST /identify/", enabled="true")
    SubElement(identifyRequest, 'boolProp', name="HTTPSampler.postBodyRaw").text = "true"
    
    elementProp = SubElement(identifyRequest, 'elementProp', name="HTTPsampler.Arguments", elementType="Arguments")
    collectionProp = SubElement(elementProp, 'collectionProp', name="Arguments.arguments")
    elementProp = SubElement(collectionProp, 'elementProp', name="", elementType="HTTPArgument")
    SubElement(elementProp, 'boolProp', name="HTTPArgument.always_encode").text = "false"
    SubElement(elementProp, 'stringProp', name="Argument.value").text = '{"image":"${TEST_IMAGE}","confidence_threshold":90}'
    SubElement(elementProp, 'stringProp', name="Argument.metadata").text = "="
    
    SubElement(identifyRequest, 'stringProp', name="HTTPSampler.domain").text = "${API_HOST}"
    SubElement(identifyRequest, 'stringProp', name="HTTPSampler.port").text = "${API_PORT}"
    SubElement(identifyRequest, 'stringProp', name="HTTPSampler.protocol").text = "${API_PROTOCOL}"
    SubElement(identifyRequest, 'stringProp', name="HTTPSampler.path").text = "/prod/identify/"
    SubElement(identifyRequest, 'stringProp', name="HTTPSampler.method").text = "POST"
    
    SubElement(threadHashTree, 'hashTree')
    
    # Assertions
    assertion = SubElement(threadHashTree, 'ResponseAssertion', guiclass="AssertionGui", testclass="ResponseAssertion", testname="Response Assertion", enabled="true")
    collectionProp = SubElement(assertion, 'collectionProp', name="Asserion.test_strings")
    SubElement(collectionProp, 'stringProp', name="49586").text = "200"
    SubElement(assertion, 'stringProp', name="Assertion.custom_message").text = ""
    SubElement(assertion, 'stringProp', name="Assertion.test_field").text = "Assertion.response_code"
    SubElement(assertion, 'boolProp', name="Assertion.assume_success").text = "false"
    SubElement(assertion, 'intProp', name="Assertion.test_type").text = "8"
    
    SubElement(threadHashTree, 'hashTree')
    
    # Duration Assertion (SLA <2s)
    durationAssertion = SubElement(threadHashTree, 'DurationAssertion', guiclass="DurationAssertionGui", testclass="DurationAssertion", testname="Duration Assertion (<2s SLA)", enabled="true")
    SubElement(durationAssertion, 'stringProp', name="DurationAssertion.duration").text = "2000"
    
    SubElement(threadHashTree, 'hashTree')
    
    # Listeners
    # Summary Report
    summaryReport = SubElement(threadHashTree, 'SummaryReport', guiclass="SummaryReport", testclass="SummaryReport", testname="Summary Report", enabled="true")
    SubElement(threadHashTree, 'hashTree')
    
    # Response Time Graph
    responseGraph = SubElement(threadHashTree, 'ResultCollector', guiclass="GraphVisualizer", testclass="ResultCollector", testname="Graph Results", enabled="true")
    SubElement(threadHashTree, 'hashTree')
    
    # View Results Tree (disabled in production)
    resultsTree = SubElement(threadHashTree, 'ResultCollector', guiclass="ViewResultsFullVisualizer", testclass="ResultCollector", testname="View Results Tree", enabled="false")
    SubElement(threadHashTree, 'hashTree')
    
    # Generate pretty XML
    rough_string = tostring(jmeterTestPlan, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    return pretty_xml


def save_jmeter_plan(filename="face_recognition_load_test.jmx"):
    """Save JMeter test plan to file"""
    
    xml_content = create_jmeter_test_plan()
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"✅ JMeter test plan saved to {filename}")
    print(f"""
To run the test:

1. Install JMeter: https://jmeter.apache.org/download_jmeter.cgi

2. Run in GUI mode (for debugging):
   jmeter -t {filename}

3. Run in CLI mode (for actual load test):
   jmeter -n -t {filename} -l results.jtl -e -o report/
   
   Parameters:
   -Japi.host=your-api-gateway.amazonaws.com
   -Japi.port=443
   -Japi.protocol=https
   -Jusers=100
   -Jrampup=60
   -Jduration=600
   
4. View HTML report:
   Open report/index.html in browser
   
Target: 100 users × 50 req/min = 5000 req/min
SLA: P95 latency < 2000ms
Duration: 10 minutes = 50,000 total requests
    """)


if __name__ == "__main__":
    save_jmeter_plan()
