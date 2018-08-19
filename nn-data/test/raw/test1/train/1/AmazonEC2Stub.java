// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

/**
 * AmazonEC2Stub.java
 *
 * This file was auto-generated from WSDL
 * by the Apache Axis2 version: 1.5.1  Built on : Oct 19, 2009 (10:59:00 EDT)
 */
        package com.amazon.ec2.client;

        

        /*
        *  AmazonEC2Stub java implementation
        */

        
        public class AmazonEC2Stub extends org.apache.axis2.client.Stub
        {
        protected org.apache.axis2.description.AxisOperation[] _operations;

        //hashmaps to keep the fault mapping
        private java.util.HashMap faultExceptionNameMap = new java.util.HashMap();
        private java.util.HashMap faultExceptionClassNameMap = new java.util.HashMap();
        private java.util.HashMap faultMessageMap = new java.util.HashMap();

        private static int counter = 0;

        private static synchronized java.lang.String getUniqueSuffix(){
            // reset the counter if it is greater than 99999
            if (counter > 99999){
                counter = 0;
            }
            counter = counter + 1; 
            return java.lang.Long.toString(System.currentTimeMillis()) + "_" + counter;
        }

    
    private void populateAxisService() throws org.apache.axis2.AxisFault {

     //creating the Service with a unique name
     _service = new org.apache.axis2.description.AxisService("AmazonEC2" + getUniqueSuffix());
     addAnonymousOperations();

        //creating the operations
        org.apache.axis2.description.AxisOperation __operation;

        _operations = new org.apache.axis2.description.AxisOperation[95];
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "registerImage"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[0]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteTags"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[1]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createKeyPair"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[2]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "terminateInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[3]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeImageAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[4]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSecurityGroups"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[5]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describePlacementGroups"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[6]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createVpnConnection"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[7]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "attachVpnGateway"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[8]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createVolume"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[9]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "releaseAddress"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[10]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeRegions"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[11]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteSubnet"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[12]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeVpcs"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[13]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSpotPriceHistory"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[14]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeReservedInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[15]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeTags"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[16]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "importVolume"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[17]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSpotDatafeedSubscription"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[18]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deactivateLicense"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[19]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "detachVolume"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[20]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeReservedInstancesOfferings"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[21]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeConversionTasks"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[22]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteCustomerGateway"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[23]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deletePlacementGroup"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[24]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "requestSpotInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[25]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "confirmProductInstance"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[26]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "modifySnapshotAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[27]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "purchaseReservedInstancesOffering"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[28]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "cancelConversionTask"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[29]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteVpnConnection"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[30]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "detachVpnGateway"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[31]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeCustomerGateways"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[32]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeLicenses"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[33]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "revokeSecurityGroupIngress"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[34]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSubnets"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[35]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "resetSnapshotAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[36]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeAddresses"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[37]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createSecurityGroup"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[38]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "allocateAddress"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[39]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "importKeyPair"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[40]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createTags"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[41]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "startInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[42]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeVpnConnections"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[43]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "rebootInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[44]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeAvailabilityZones"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[45]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "bundleInstance"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[46]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "activateLicense"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[47]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSnapshots"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[48]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createPlacementGroup"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[49]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSpotInstanceRequests"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[50]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "associateAddress"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[51]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "runInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[52]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteSecurityGroup"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[53]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteVpc"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[54]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteVolume"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[55]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createVpnGateway"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[56]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "resetInstanceAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[57]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createVpc"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[58]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteKeyPair"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[59]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "stopInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[60]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createImage"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[61]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeVolumes"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[62]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeKeyPairs"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[63]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createCustomerGateway"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[64]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeImages"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[65]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createSubnet"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[66]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "disassociateAddress"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[67]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "deleteVpnGateway"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[68]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "cancelSpotInstanceRequests"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[69]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "monitorInstances"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[70]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "createSnapshot"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[71]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "resetImageAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[72]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "attachVolume"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[73]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeInstanceAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[74]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "authorizeSecurityGroupIngress"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[75]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "modifyInstanceAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[76]=__operation;
            
        
                   __operation = new org.apache.axis2.description.OutInAxisOperation();
                

            __operation.setName(new javax.xml.namespace.QName("http://ec2.amazonaws.com/doc/2010-11-15/", "describeSnapshotAttribute"));
	    _service.addOperation(__operation);
	    

	    
	    
            _operations[77]=__operation;
            
