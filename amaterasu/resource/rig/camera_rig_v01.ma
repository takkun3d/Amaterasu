//Maya ASCII 2022 scene
//Name: camera_rig_v01c.ma
//Last modified: Fri, Dec 13, 2024 01:36:18 AM
//Codeset: 932
requires maya "2022";
requires "stereoCamera" "10.0";
requires "mtoa" "5.0.0.1";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2022";
fileInfo "version" "2022";
fileInfo "cutIdentifier" "202110272215-ad32f8f1e6";
fileInfo "osv" "Windows 10 Home v2009 (Build: 22631)";
fileInfo "UUID" "A55C2462-4B3B-9E51-BA31-03B3D875CB05";
createNode transform -n "camera_grp";
	rename -uid "E1282867-4D91-6CBB-DDE3-2E8F09A82E37";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "render_cam" -p "camera_grp";
	rename -uid "376CD194-42C6-5A30-4128-23AC97BE6D12";
createNode camera -n "render_camShape" -p "render_cam";
	rename -uid "1B345B72-4F74-2DE7-14F6-34B29B97E364";
	setAttr -k off ".v";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr -l on ".ff";
	setAttr ".ovr" 1.3;
	setAttr ".ncp" 10;
	setAttr ".fcp" 100;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
	setAttr ".dr" yes;
	setAttr ".bfc" no;
	setAttr ".dgc" -type "float3" 0 0 0 ;
createNode transform -n "controller_grp" -p "camera_grp";
	rename -uid "635A669F-49EB-3BDC-9092-3EBCC4DC0AB7";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "root_C_ctrl" -p "controller_grp";
	rename -uid "7BA62004-44D5-C5FC-C90A-3AB20B8CB564";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 13;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0 0 ;
createNode nurbsCurve -n "root_C_ctrlShape" -p "root_C_ctrl";
	rename -uid "5C7732FE-4C6E-965D-ABD4-27A6F9D8295D";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode transform -n "local_C_ctrl" -p "root_C_ctrl";
	rename -uid "B54C0643-4511-3A2C-7E53-D0965A010895";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 6;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.16666669 0 ;
createNode nurbsCurve -n "local_C_ctrlShape" -p "local_C_ctrl";
	rename -uid "BA55FD7F-4BEF-5A3F-E056-C9B84A766F75";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode transform -n "body_C_ctrl" -p "local_C_ctrl";
	rename -uid "2DB14898-443C-C600-4A60-69B74FE2EE05";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 17;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.33333337 0 ;
createNode nurbsCurve -n "body_C_ctrlShape" -p "body_C_ctrl";
	rename -uid "02573531-44D7-7CB6-45AB-BC99CDA14E4A";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode transform -n "camera_C_ctrl" -p "body_C_ctrl";
	rename -uid "D0B4C45D-4CBE-48B1-625C-4FBDA75F6381";
	addAttr -ci true -sn "camera" -ln "camera" -nn "--------------------" -min 0 -max 
		0 -en "Camera" -at "enum";
	addAttr -ci true -sn "focalLength" -ln "focalLength" -dv 1 -min 1 -at "double";
	addAttr -ci true -sn "shake" -ln "shake" -nn "--------------------" -min 0 -max 
		0 -en "Shake" -at "enum";
	addAttr -ci true -sn "enableShake" -ln "enableShake" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTX" -ln "enableTX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTY" -ln "enableTY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTZ" -ln "enableTZ" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableRX" -ln "enableRX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableRY" -ln "enableRY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableRZ" -ln "enableRZ" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "noiseA" -ln "noiseA" -nn "--------------------" -min 0 -max 
		0 -en "Noise A" -at "enum";
	addAttr -ci true -sn "enableNoiseA" -ln "enableNoiseA" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedA" -ln "seedA" -at "double";
	addAttr -ci true -sn "speedA" -ln "speedA" -at "double";
	addAttr -ci true -sn "magnitudeA" -ln "magnitudeA" -at "double";
	addAttr -ci true -sn "noiseB" -ln "noiseB" -nn "--------------------" -min 0 -max 
		0 -en "Noise B" -at "enum";
	addAttr -ci true -sn "enableNoiseB" -ln "enableNoiseB" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedB" -ln "seedB" -at "double";
	addAttr -ci true -sn "speedB" -ln "speedB" -at "double";
	addAttr -ci true -sn "magnitudeB" -ln "magnitudeB" -at "double";
	addAttr -ci true -sn "noiseC" -ln "noiseC" -nn "--------------------" -min 0 -max 
		0 -en "Noise C" -at "enum";
	addAttr -ci true -sn "enableNoiseC" -ln "enableNoiseC" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedC" -ln "seedC" -at "double";
	addAttr -ci true -sn "speedC" -ln "speedC" -at "double";
	addAttr -ci true -sn "magnitudeC" -ln "magnitudeC" -at "double";
	addAttr -ci true -sn "noiseD" -ln "noiseD" -nn "--------------------" -min 0 -max 
		0 -en "Noise D" -at "enum";
	addAttr -ci true -sn "enableNoiseD" -ln "enableNoiseD" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedD" -ln "seedD" -at "double";
	addAttr -ci true -sn "speedD" -ln "speedD" -at "double";
	addAttr -ci true -sn "magnitudeD" -ln "magnitudeD" -at "double";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 27;
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.5 0 ;
	setAttr -k on ".camera";
	setAttr -k on ".focalLength" 35;
	setAttr -k on ".shake";
	setAttr -k on ".enableShake";
	setAttr -k on ".enableTX" yes;
	setAttr -k on ".enableTY" yes;
	setAttr -k on ".enableTZ";
	setAttr -k on ".enableRX" yes;
	setAttr -k on ".enableRY" yes;
	setAttr -k on ".enableRZ";
	setAttr -k on ".noiseA";
	setAttr -k on ".enableNoiseA" yes;
	setAttr -k on ".seedA" 3;
	setAttr -k on ".speedA" 0.1;
	setAttr -k on ".magnitudeA" 1;
	setAttr -k on ".noiseB";
	setAttr -k on ".enableNoiseB" yes;
	setAttr -k on ".seedB" 4;
	setAttr -k on ".speedB" 1;
	setAttr -k on ".magnitudeB" 0.1;
	setAttr -k on ".noiseC";
	setAttr -k on ".enableNoiseC" yes;
	setAttr -k on ".seedC" 5;
	setAttr -k on ".speedC" 0.1;
	setAttr -k on ".magnitudeC" 5;
	setAttr -k on ".noiseD";
	setAttr -k on ".enableNoiseD" yes;
	setAttr -k on ".seedD" 6;
	setAttr -k on ".speedD" 1;
	setAttr -k on ".magnitudeD" 1;
createNode nurbsCurve -n "camera_C_ctrlShapeOrg" -p "camera_C_ctrl";
	rename -uid "C4EEA3DA-4152-E36F-75B2-14A9E98623A6";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 71 0 no 3
		72 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54
		 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71
		72
		1.0047097279177222e-06 -2.2474945433981572 -2.9730335432451982
		0.43846639643248586 -2.204308892561111 -2.9730335432451982
		0.86007881443005063 -2.0764128401784432 -2.9730335432451982
		1.248641792117505 -1.8687216617318412 -2.9730335432451982
		1.5892184658225617 -1.5892184658225639 -2.9730335432451982
		1.8687239092286299 -1.2486395446207164 -2.9730335432451982
		2.0764150876752319 -0.86007881443005285 -2.9730335432451991
		2.2043088925611087 -0.43846414893569724 -2.9730335432451991
		2.2474967908949459 -2.2204462348704405e-15 -2.9730335432451991
		2.2043111400578996 0.4384641489356928 -2.9730335432451991
		2.0764150876752319 0.86007881443004841 -2.9730335432451991
		1.8687239092286299 1.2486417921175028 -2.9730335432452
		1.5892207133193526 1.5892207133193503 -2.9730335432452
		1.248641792117505 1.8687261567254185 -2.9730335432452
		0.86007881443005063 2.0764150876752296 -2.9730335432452
		0.43846414893569502 2.2043111400578974 -2.9730335432452
		-3.6839394148596327e-07 2.2474967908949437 -2.9730335432452
		-0.43846414893569502 2.2043111400578974 -2.9730335432452
		-0.86007881443005063 2.0764150876752296 -2.9730335432452
		-1.248641792117505 1.8687239092286276 -2.9730335432452
		-1.5892207133193526 1.5892184658225594 -2.9730335432452
		-1.8687239092286299 1.2486417921175028 -2.9730335432452
		-2.0764150876752319 0.86007881443004841 -2.9730335432451991
		-2.2043111400578996 0.4384641489356928 -2.9730335432451991
		-2.247494543398155 -7.367878851923728e-07 -2.9730335432451991
		-2.2043111400578996 -0.43846639643248808 -2.9730335432451991
		-2.0764150876752319 -0.86007881443005285 -2.9730335432451991
		-1.8687239092286299 -1.2486417921175073 -2.9730335432451982
		-1.5892184658225617 -1.5892184658225639 -2.9730335432451982
		-1.2486395446207141 -1.8687239092286321 -2.9730335432451982
		-0.86007881443005063 -2.0764150876752341 -2.9730335432451982
		-0.43846414893569502 -2.204308892561111 -2.9730335432451982
		1.0047097279177222e-06 -2.2474945433981572 -2.9730335432451982
		1.0047097279177222e-06 -2.247494543398155 7.4856580741774194e-16
		0.43846639643248586 -2.2043088925611087 7.2938752586065736e-16
		0.86007881443005063 -2.076412840178441 6.7259026901509621e-16
		1.248641792117505 -1.868721661731839 5.8035685768591637e-16
		1.5892184658225617 -1.5892184658225617 4.5623250426399816e-16
		1.8687239092286299 -1.2486395446207141 3.0498508025588296e-16
		2.0764150876752319 -0.86007881443005063 1.3242945260674783e-16
		2.2043088925611087 -0.43846414893569502 -5.4805071053839009e-17
		2.2474967908949459 1.8562012677248409e-22 -2.4952226850227198e-16
		2.2474967908949459 -2.2204462348704405e-15 -2.9730335432451991
		2.2474967908949459 1.8562012677248409e-22 -2.4952226850227198e-16
		2.2043111400578996 0.43846414893569502 -4.4423946595070498e-16
		2.0764150876752319 0.86007881443005063 -6.314739896112918e-16
		1.8687239092286299 1.248641792117505 -8.0403061534950094e-16
		1.5892207133193526 1.5892207133193526 -9.5527803935761614e-16
		1.248641792117505 1.8687261567254208 -1.0794033908686084e-15
		0.86007881443005063 2.0764150876752319 -1.1716358041087142e-15
		0.43846414893569502 2.2043111400578996 -1.2284330609542753e-15
		-3.6839394148596327e-07 2.2474967908949459 -1.2476113425113599e-15
		-3.6839394148596327e-07 2.2474967908949437 -2.9730335432452
		-3.6839394148596327e-07 2.2474967908949459 -1.2476113425113599e-15
		-0.43846414893569502 2.2043111400578996 -1.2284330609542753e-15
		-0.86007881443005063 2.0764150876752319 -1.1716358041087142e-15
		-1.248641792117505 1.8687239092286299 -1.0794023927795344e-15
		-1.5892207133193526 1.5892184658225617 -9.5527704126854213e-16
		-1.8687239092286299 1.248641792117505 -8.0403061534950094e-16
		-2.0764150876752319 0.86007881443005063 -6.314739896112918e-16
		-2.2043111400578996 0.43846414893569502 -4.4423946595070498e-16
		-2.247494543398155 -7.3678788297192622e-07 -2.4952194130272323e-16
		-2.247494543398155 -7.367878851923728e-07 -2.9730335432451991
		-2.247494543398155 -7.3678788297192622e-07 -2.4952194130272323e-16
		-2.2043111400578996 -0.43846639643248586 -5.4804072964765024e-17
		-2.0764150876752319 -0.86007881443005063 1.3242945260674783e-16
		-1.8687239092286299 -1.248641792117505 3.0498607834495697e-16
		-1.5892184658225617 -1.5892184658225617 4.5623250426399816e-16
		-1.2486395446207141 -1.8687239092286299 5.8035785577499038e-16
		-0.86007881443005063 -2.0764150876752319 6.7259126710417022e-16
		-0.43846414893569502 -2.2043088925611087 7.2938752586065736e-16
		1.0047097279177222e-06 -2.247494543398155 7.4856580741774194e-16
		;
createNode nurbsCurve -n "camera_C_ctrlShape" -p "camera_C_ctrl";
	rename -uid "1C2023ED-4061-5F08-A3E0-7E952B1E9E3A";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode nurbsCurve -n "camera_C_ctrlShape1" -p "camera_C_ctrl";
	rename -uid "9DCAE9B5-4BBD-7116-F589-E0A0FE4D82F7";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode nurbsCurve -n "camera_C_ctrlShape1Org" -p "camera_C_ctrl";
	rename -uid "A068744B-4FA2-0389-CC31-23A1F57AAFC4";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 15 0 no 3
		16 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
		16
		2.1375624769945145 5 12.763369361662779
		-2.1375624769945145 5 12.763369361662779
		-2.1375624769945145 5 0
		2.1375624769945145 5 0
		2.1375624769945145 5 12.763369361662779
		2.1375624769945145 -3.4031123886933572 12.763369361662779
		2.1375624769945145 -3.4031123886933572 0
		2.1375624769945145 5 0
		2.1375624769945145 -3.4031123886933572 0
		-2.1375624769945145 -3.4031123886933572 0
		-2.1375624769945145 5 0
		-2.1375624769945145 -3.4031123886933572 0
		-2.1375624769945145 -3.4031123886933572 12.763369361662779
		-2.1375624769945145 5 12.763369361662779
		-2.1375624769945145 -3.4031123886933572 12.763369361662779
		2.1375624769945145 -3.4031123886933572 12.763369361662779
		;
createNode nurbsCurve -n "body_C_ctrlShapeOrg" -p "body_C_ctrl";
	rename -uid "348C932E-4E49-D466-D139-109BCAAC69F8";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 24 2 no 3
		25 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
		25
		0 0 -6.5
		1.9499999999999995 0 -3.25
		0.97499999999999976 0 -3.25
		0.97499999999999976 0 -0.97499999999999976
		3.25 0 -0.97499999999999976
		3.25 0 -1.9499999999999995
		6.5 0 0
		3.25 0 1.9499999999999995
		3.25 0 0.97499999999999976
		0.97499999999999976 0 0.97499999999999976
		0.97499999999999976 0 3.25
		1.9499999999999995 0 3.25
		0 0 6.5
		-1.9499999999999995 0 3.25
		-0.97499999999999976 0 3.25
		-0.97499999999999976 0 0.97499999999999976
		-3.25 0 0.97499999999999976
		-3.25 0 1.9499999999999995
		-6.5 0 0
		-3.25 0 -1.9499999999999995
		-3.25 0 -0.97499999999999976
		-0.97499999999999976 0 -0.97499999999999976
		-0.97499999999999976 0 -3.25
		-1.9499999999999995 0 -3.25
		0 0 -6.5
		;
createNode nurbsCurve -n "local_C_ctrlShapeOrg" -p "local_C_ctrl";
	rename -uid "0FAA3BB9-4EB3-1122-728B-058A07101517";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 12 2 no 3
		13 0 1 2 3 4 5 6 7 8 9 10 11 12
		13
		3.5 0 -7
		3.5 0 -3.5
		7 0 -3.5
		7 0 3.5
		3.5 0 3.5
		3.5 0 7
		-3.5 0 7
		-3.5 0 3.5
		-7 0 3.5
		-7 0 -3.5
		-3.5 0 -3.5
		-3.5 0 -7
		3.5 0 -7
		;
createNode nurbsCurve -n "root_C_ctrlShapeOrg" -p "root_C_ctrl";
	rename -uid "518B0A1B-4934-465E-5144-89960E60BA53";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 32 2 no 3
		33 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32
		33
		0 0 -10
		1.5607199999999999 0 -7.8462800000000001
		3.0614699999999999 0 -7.3910400000000003
		4.4445600000000001 0 -6.6517599999999995
		5.6568500000000004 0 -5.6568500000000004
		6.6517599999999995 0 -4.4445600000000001
		7.3910299999999998 0 -3.0614699999999999
		7.8462800000000001 0 -1.5607199999999999
		8 0 1.3112999999999998e-06
		7.8462800000000001 0 1.5607199999999999
		7.3910299999999998 0 3.0614699999999999
		6.6517499999999998 0 4.4445600000000001
		5.6568500000000004 0 5.6568500000000004
		4.4445600000000001 0 6.6517499999999998
		3.0614599999999998 0 7.3910299999999998
		1.5607199999999999 0 7.8462800000000001
		-2.6226000000000001e-06 0 7.9999900000000004
		-1.5607199999999999 0 7.8462800000000001
		-3.0614699999999999 0 7.3910299999999998
		-4.4445600000000001 0 6.6517499999999998
		-5.6568500000000004 0 5.6568500000000004
		-6.6517499999999998 0 4.4445600000000001
		-7.3910299999999998 0 3.0614599999999998
		-7.8462800000000001 0 1.5607199999999999
		-7.9999900000000004 0 -3.5762800000000003e-06
		-7.8462699999999996 0 -1.5607199999999999
		-7.3910299999999998 0 -3.0614699999999999
		-6.6517499999999998 0 -4.4445600000000001
		-5.6568500000000004 0 -5.6568500000000004
		-4.4445499999999996 0 -6.6517499999999998
		-3.0614599999999998 0 -7.3910299999999998
		-1.5607199999999999 0 -7.8462699999999996
		0 0 -10
		;
createNode transform -n "filmOffsetSlider_C_ctrl" -p "controller_grp";
	rename -uid "0DA09682-4216-A909-01E5-E49761CA552D";
	addAttr -ci true -sn "shake" -ln "shake" -nn "--------------------" -min 0 -max 
		0 -en "Shake" -at "enum";
	addAttr -ci true -sn "enableShake" -ln "enableShake" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTX" -ln "enableTX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTY" -ln "enableTY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "noiseA" -ln "noiseA" -nn "--------------------" -min 0 -max 
		0 -en "Noise A" -at "enum";
	addAttr -ci true -sn "enableNoiseA" -ln "enableNoiseA" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedA" -ln "seedA" -at "double";
	addAttr -ci true -sn "speedA" -ln "speedA" -at "double";
	addAttr -ci true -sn "magnitudeA" -ln "magnitudeA" -at "double";
	addAttr -ci true -sn "noiseB" -ln "noiseB" -nn "--------------------" -min 0 -max 
		0 -en "Noise B" -at "enum";
	addAttr -ci true -sn "enableNoiseB" -ln "enableNoiseB" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedB" -ln "seedB" -at "double";
	addAttr -ci true -sn "speedB" -ln "speedB" -at "double";
	addAttr -ci true -sn "magnitudeB" -ln "magnitudeB" -at "double";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 17;
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 1 0 ;
	setAttr -k on ".shake";
	setAttr -k on ".enableShake";
	setAttr -k on ".enableTX" yes;
	setAttr -k on ".enableTY" yes;
	setAttr -k on ".noiseA";
	setAttr -k on ".enableNoiseA" yes;
	setAttr -k on ".seedA" 1;
	setAttr -k on ".speedA" 0.3;
	setAttr -k on ".magnitudeA" 0.1;
	setAttr -k on ".noiseB";
	setAttr -k on ".enableNoiseB" yes;
	setAttr -k on ".seedB" 2;
	setAttr -k on ".speedB" 1;
	setAttr -k on ".magnitudeB" 0.01;
createNode nurbsCurve -n "filmOffsetSlider_C_ctrlShape" -p "filmOffsetSlider_C_ctrl";
	rename -uid "6C63E6E8-4DD3-506A-3B2C-4DA04BB4A1C2";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.023508348746736737 0.023508348746736737 -1.040834085586084e-18
		2.035719696933274e-18 0.033245825626631635 3.1225022567582528e-18
		-0.023508348746736737 0.023508348746736737 1.0408340855860846e-18
		-0.033245825626631649 1.723469471257449e-18 9.6046896495009709e-34
		-0.023508348746736737 -0.023508348746736737 -1.040834085586084e-18
		-3.330257090880968e-18 -0.033245825626631656 -1.040834085586084e-18
		0.023508348746736737 -0.023508348746736737 -1.040834085586084e-18
		0.033245825626631649 -4.5337215023398788e-18 6.7157947329201171e-34
		0.023508348746736737 0.023508348746736737 -1.040834085586084e-18
		2.035719696933274e-18 0.033245825626631635 3.1225022567582528e-18
		-0.023508348746736737 0.023508348746736737 1.0408340855860846e-18
		;
createNode transform -n "aimTarget_C_ctrl" -p "controller_grp";
	rename -uid "89F756DE-46BF-804E-A58E-D693AB0BF7EB";
	addAttr -ci true -sn "aimOption" -ln "aimOption" -nn "--------------------" -min 
		0 -max 0 -en "Aim" -at "enum";
	addAttr -ci true -sn "parent" -ln "parent" -min 0 -max 4 -en "Camera:Body:Local:Root:None" 
		-at "enum";
	addAttr -ci true -sn "aim" -ln "aim" -min 0 -max 1 -at "double";
	addAttr -ci true -sn "roll" -ln "roll" -at "double";
	addAttr -ci true -sn "shake" -ln "shake" -nn "--------------------" -min 0 -max 
		0 -en "Shake" -at "enum";
	addAttr -ci true -sn "enableShake" -ln "enableShake" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTX" -ln "enableTX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTY" -ln "enableTY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "enableTZ" -ln "enableTZ" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "noiseA" -ln "noiseA" -nn "--------------------" -min 0 -max 
		0 -en "Noise A" -at "enum";
	addAttr -ci true -sn "enableNoiseA" -ln "enableNoiseA" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedA" -ln "seedA" -at "double";
	addAttr -ci true -sn "speedA" -ln "speedA" -at "double";
	addAttr -ci true -sn "magnitudeA" -ln "magnitudeA" -at "double";
	addAttr -ci true -sn "noiseB" -ln "noiseB" -nn "--------------------" -min 0 -max 
		0 -en "Noise B" -at "enum";
	addAttr -ci true -sn "enableNoiseB" -ln "enableNoiseB" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "seedB" -ln "seedB" -at "double";
	addAttr -ci true -sn "speedB" -ln "speedB" -at "double";
	addAttr -ci true -sn "magnitudeB" -ln "magnitudeB" -at "double";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 13;
	setAttr ".t" -type "double3" 0 0 2.8421709430404007e-14 ;
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0 1 0 ;
	setAttr -k on ".aimOption";
	setAttr -k on ".parent" 1;
	setAttr -k on ".aim";
	setAttr -k on ".roll" 3.8000000000000003;
	setAttr -k on ".shake";
	setAttr -k on ".enableShake";
	setAttr -k on ".enableTX" yes;
	setAttr -k on ".enableTY" yes;
	setAttr -k on ".enableTZ";
	setAttr -k on ".noiseA";
	setAttr -k on ".enableNoiseA" yes;
	setAttr -k on ".seedA" 7;
	setAttr -k on ".speedA" 0.1;
	setAttr -k on ".magnitudeA" 10;
	setAttr -k on ".noiseB";
	setAttr -k on ".enableNoiseB" yes;
	setAttr -k on ".seedB" 8;
	setAttr -k on ".speedB" 1;
	setAttr -k on ".magnitudeB" 1;
createNode nurbsCurve -n "aimTarget_C_ctrlShape" -p "aimTarget_C_ctrl";
	rename -uid "0E118DED-45A8-250F-3269-3E8A676D8922";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode nurbsCurve -n "aimTarget_C_ctrlShape1" -p "aimTarget_C_ctrl";
	rename -uid "235BA668-4266-0558-2858-A6BCE7405FE1";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode nurbsCurve -n "aimTarget_C_ctrlShape2" -p "aimTarget_C_ctrl";
	rename -uid "C338C829-484D-0007-1ED3-FA91908A45E6";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode nurbsCurve -n "aimTarget_C_ctrlShapeOrg" -p "aimTarget_C_ctrl";
	rename -uid "9D707C64-423D-3E31-AE09-ED88703AC63C";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		2 0 0
		-2 0 0
		;
createNode nurbsCurve -n "aimTarget_C_ctrlShape1Org" -p "aimTarget_C_ctrl";
	rename -uid "A5C5DA08-4240-72E9-F6DE-3881EA1F6BEF";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 2 0
		0 -2 0
		;
createNode nurbsCurve -n "aimTarget_C_ctrlShape2Org" -p "aimTarget_C_ctrl";
	rename -uid "76EAF210-44E1-3D35-0BFE-9FB48338FAD5";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		0 0 2
		0 0 -2
		;
createNode transform -n "nearClipPlane_C_ctrl" -p "controller_grp";
	rename -uid "BC3CAA69-4C31-C0B3-9EB1-928D3AF8ECC8";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 20;
	setAttr ".t" -type "double3" 0 0 10 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0 1 1 ;
createNode nurbsCurve -n "nearClipPlane_C_ctrlShape" -p "nearClipPlane_C_ctrl";
	rename -uid "E31C6C40-453E-2F68-01E3-0285267F3B41";
	setAttr -k off ".v";
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 2 no 3
		5 0 1 2 3 4
		5
		0.5 0.5 -8.3266726846886741e-17
		0.5 -0.5 8.3266726846886741e-17
		-0.5 -0.5 8.3266726846886741e-17
		-0.5 0.5 -8.3266726846886741e-17
		0.5 0.5 -8.3266726846886741e-17
		;
createNode transform -n "farClipPlane_C_ctrl" -p "controller_grp";
	rename -uid "B95EEF27-422C-3A21-6978-F3A144CDB4C8";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 18;
	setAttr ".t" -type "double3" 0 0 100 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0 1 1 ;
createNode nurbsCurve -n "farClipPlane_C_ctrlShape" -p "farClipPlane_C_ctrl";
	rename -uid "CE210DF8-474F-7089-3EE8-F2837C8CB96B";
	setAttr -k off ".v";
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 2 no 3
		5 0 1 2 3 4
		5
		0.5 0.49999999999999994 -8.3266726846886741e-17
		0.5 -0.49999999999999994 8.3266726846886741e-17
		-0.5 -0.49999999999999994 8.3266726846886741e-17
		-0.5 0.49999999999999994 -8.3266726846886741e-17
		0.5 0.49999999999999994 -8.3266726846886741e-17
		;
createNode transform -n "settings_C_ctrl" -p "controller_grp";
	rename -uid "76F6806E-4C06-5736-27F0-CD87CC662939";
	addAttr -ci true -sn "display" -ln "display" -nn "--------------------" -min 0 -max 
		0 -en "Display" -at "enum";
	addAttr -ci true -sn "rigSize" -ln "rigSize" -dv 0.0001 -min 0.0001 -at "double";
	addAttr -ci true -sn "gateOpacity" -ln "gateOpacity" -min 0 -max 1 -at "double";
	addAttr -ci true -sn "playblack" -ln "playblack" -nn "--------------------" -min 
		0 -max 0 -en "Playblack" -at "enum";
	addAttr -ci true -sn "hideRigOnPlayblack" -ln "hideRigOnPlayblack" -min 0 -max 1 
		-at "bool";
	addAttr -ci true -sn "hideGuideOnPlayblack" -ln "hideGuideOnPlayblack" -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "Guide" -ln "Guide" -nn "--------------------" -min 0 -max 
		0 -en "Guide" -at "enum";
	addAttr -ci true -sn "gridGuide" -ln "gridGuide" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "perspectiveGuide" -ln "perspectiveGuide" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "verticalGuideOffset" -ln "verticalGuideOffset" -at "double";
	setAttr -l on -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 9;
	setAttr ".t" -type "double3" 0 15 0 ;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0 1 ;
	setAttr -k on ".playblack";
	setAttr -k on ".hideRigOnPlayblack" yes;
	setAttr -k on ".hideGuideOnPlayblack";
	setAttr -k on ".Guide";
	setAttr -k on ".gridGuide" yes;
	setAttr -k on ".perspectiveGuide" yes;
	setAttr -k on ".verticalGuideOffset";
	setAttr -k on ".display";
	setAttr -k on ".gateOpacity" 1;
	setAttr -k on ".rigSize" 1;
createNode nurbsCurve -n "settings_C_ctrlShape" -p "settings_C_ctrl";
	rename -uid "1B1E421F-46C9-FA67-7E4F-56A1F6843F1A";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 40 2 no 3
		41 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32 33 34 35 36 37 38 39 40
		41
		-0.140012 1 4.4408920985006262e-16
		0.140013 1 4.4408920985006262e-16
		0.17386199999999999 0.80000000000000004 3.5527136788005011e-16
		0.31214500000000001 0.753583 3.3465807902643974e-16
		0.442747 0.68862400000000001 3.0581048804378953e-16
		0.60810399999999998 0.80610999999999999 3.5798475295223397e-16
		0.80611100000000002 0.60810299999999995 2.700519807774526e-16
		0.68862500000000004 0.442747 1.9661916539348567e-16
		0.75358400000000003 0.31214399999999998 1.3861978231943794e-16
		0.80000099999999996 0.17386099999999999 7.7209794113741731e-17
		1.0000009999999999 0.140012 6.2177818449526966e-17
		1.0000009999999999 -0.140013 -6.2178262538736816e-17
		0.80000099999999996 -0.17386199999999999 -7.7210238202951582e-17
		0.75358400000000003 -0.31214500000000001 -1.386202264086478e-16
		0.68862500000000004 -0.442747 -1.9661916539348567e-16
		0.80611100000000002 -0.60810399999999998 -2.7005242486666247e-16
		0.60810399999999998 -0.80611100000000002 -3.5798519704144384e-16
		0.442747 -0.68862500000000004 -3.0581093213299939e-16
		0.31214500000000001 -0.75358400000000003 -3.346585231156496e-16
		0.17386199999999999 -0.80000099999999996 -3.5527181196925993e-16
		0.140013 -1.0000009999999999 -4.4408965393927243e-16
		-0.140012 -1.0000009999999999 -4.4408965393927243e-16
		-0.17386099999999999 -0.80000099999999996 -3.5527181196925993e-16
		-0.31214399999999998 -0.75358400000000003 -3.346585231156496e-16
		-0.442747 -0.68862500000000004 -3.0581093213299939e-16
		-0.60810299999999995 -0.80611100000000002 -3.5798519704144384e-16
		-0.80610999999999999 -0.60810399999999998 -2.7005242486666247e-16
		-0.68862400000000001 -0.442747 -1.9661916539348567e-16
		-0.753583 -0.31214500000000001 -1.386202264086478e-16
		-0.80000000000000004 -0.17386199999999999 -7.7210238202951582e-17
		-1 -0.140013 -6.2178262538736816e-17
		-1 0.140012 6.2177818449526966e-17
		-0.80000000000000004 0.17386099999999999 7.7209794113741731e-17
		-0.753583 0.31214399999999998 1.3861978231943794e-16
		-0.68862400000000001 0.442747 1.9661916539348567e-16
		-0.80610999999999999 0.60810299999999995 2.700519807774526e-16
		-0.60810299999999995 0.80610999999999999 3.5798475295223397e-16
		-0.442747 0.68862400000000001 3.0581048804378953e-16
		-0.31214399999999998 0.75358400000000003 3.346585231156496e-16
		-0.17386099999999999 0.80000000000000004 3.5527136788005011e-16
		-0.140012 1 4.4408920985006262e-16
		;
createNode nurbsCurve -n "settings_C_ctrlShape1" -p "settings_C_ctrl";
	rename -uid "1718DB6E-4F51-723D-95B9-6791D034F84E";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 32 2 no 3
		33 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
		 28 29 30 31 32
		33
		-1.7122400000000001e-09 0.30587700000000001 1.3583667524130761e-16
		0.059673700000000003 0.29999999999999999 1.3322676295501878e-16
		0.11705400000000001 0.28259400000000001 1.254969461683686e-16
		0.169937 0.254328 1.1294432056274672e-16
		0.21628800000000001 0.21628800000000001 9.6051167020050347e-17
		0.254328 0.169936 7.5466743965080242e-17
		0.28259400000000001 0.11705400000000001 5.1982418369789232e-17
		0.29999999999999999 0.059673700000000003 2.6500446281829683e-17
		0.30587799999999998 1.7122400000000001e-09 7.6038730867367125e-25
		0.29999999999999999 -0.059673700000000003 -2.6500446281829683e-17
		0.28259499999999999 -0.11705400000000001 -5.1982418369789232e-17
		0.254328 -0.169937 -7.5467188054290093e-17
		0.21628900000000001 -0.21628800000000001 -9.6051167020050347e-17
		0.169937 -0.254328 -1.1294432056274672e-16
		0.11705500000000001 -0.28259400000000001 -1.254969461683686e-16
		0.059674400000000002 -0.29999999999999999 -1.3322676295501878e-16
		6.7020899999999999e-07 -0.30587799999999998 -1.3583711933051745e-16
		-0.0596731 -0.29999999999999999 -1.3322676295501878e-16
		-0.11705400000000001 -0.28259400000000001 -1.254969461683686e-16
		-0.169936 -0.254328 -1.1294432056274672e-16
		-0.21628700000000001 -0.21628900000000001 -9.6051611109260197e-17
		-0.25432700000000003 -0.169937 -7.5467188054290093e-17
		-0.28259400000000001 -0.11705500000000001 -5.1982862458999082e-17
		-0.29999999999999999 -0.059674400000000002 -2.6500757144276578e-17
		-0.30587700000000001 -6.7020899999999999e-07 -2.9763258524440061e-22
		-0.29999999999999999 0.0596731 2.6500179828303771e-17
		-0.28259400000000001 0.11705400000000001 5.1982418369789232e-17
		-0.254328 0.169936 7.5466743965080242e-17
		-0.21628800000000001 0.21628700000000001 9.6050722930840496e-17
		-0.169936 0.25432700000000003 1.1294387647353689e-16
		-0.11705400000000001 0.28259299999999998 1.2549650207915874e-16
		-0.059673700000000003 0.29999999999999999 1.3322676295501878e-16
		-1.7122400000000001e-09 0.30587700000000001 1.3583667524130761e-16
		;
createNode transform -n "guide_grp" -p "camera_grp";
	rename -uid "85CA6F6E-45E3-F203-07D1-0BB1945E4123";
	setAttr ".uocol" yes;
createNode transform -n "aimUpTarget_C_null" -p "guide_grp";
	rename -uid "7107760D-4155-98AB-7AE4-BC93A8E69C60";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode transform -n "shakeCamera_null" -p "guide_grp";
	rename -uid "66C87827-49E4-9443-5220-1280EF41F546";
	addAttr -ci true -sn "proxyEnableShake" -ln "proxyEnableShake" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableNoiseA" -ln "proxyEnableNoiseA" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedA" -ln "proxySeedA" -at "double";
	addAttr -ci true -sn "proxySpeedA" -ln "proxySpeedA" -at "double";
	addAttr -ci true -sn "proxyMagnitudeA" -ln "proxyMagnitudeA" -at "double";
	addAttr -ci true -sn "proxyEnableNoiseB" -ln "proxyEnableNoiseB" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedB" -ln "proxySeedB" -at "double";
	addAttr -ci true -sn "proxySpeedB" -ln "proxySpeedB" -at "double";
	addAttr -ci true -sn "proxyMagnitudeB" -ln "proxyMagnitudeB" -at "double";
	addAttr -ci true -sn "proxyEnableNoiseC" -ln "proxyEnableNoiseC" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedC" -ln "proxySeedC" -at "double";
	addAttr -ci true -sn "proxySpeedC" -ln "proxySpeedC" -at "double";
	addAttr -ci true -sn "proxyMagnitudeC" -ln "proxyMagnitudeC" -at "double";
	addAttr -ci true -sn "proxyEnableNoiseD" -ln "proxyEnableNoiseD" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedD" -ln "proxySeedD" -at "double";
	addAttr -ci true -sn "proxySpeedD" -ln "proxySpeedD" -at "double";
	addAttr -ci true -sn "proxyMagnitudeD" -ln "proxyMagnitudeD" -at "double";
	addAttr -ci true -sn "proxyEnableTX" -ln "proxyEnableTX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableTY" -ln "proxyEnableTY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableTZ" -ln "proxyEnableTZ" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableRX" -ln "proxyEnableRX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableRY" -ln "proxyEnableRY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableRZ" -ln "proxyEnableRZ" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -k on ".proxyEnableShake";
	setAttr -k on ".proxyEnableNoiseA";
	setAttr -k on ".proxySeedA";
	setAttr -k on ".proxySpeedA";
	setAttr -k on ".proxyMagnitudeA";
	setAttr -k on ".proxyEnableNoiseB";
	setAttr -k on ".proxySeedB";
	setAttr -k on ".proxySpeedB";
	setAttr -k on ".proxyMagnitudeB";
	setAttr -k on ".proxyEnableNoiseC";
	setAttr -k on ".proxySeedC";
	setAttr -k on ".proxySpeedC";
	setAttr -k on ".proxyMagnitudeC";
	setAttr -k on ".proxyEnableNoiseD";
	setAttr -k on ".proxySeedD";
	setAttr -k on ".proxySpeedD";
	setAttr -k on ".proxyMagnitudeD";
	setAttr -k on ".proxyEnableTX";
	setAttr -k on ".proxyEnableTY";
	setAttr -k on ".proxyEnableTZ";
	setAttr -k on ".proxyEnableRX";
	setAttr -k on ".proxyEnableRY";
	setAttr -k on ".proxyEnableRZ";
createNode transform -n "shakeAimTarget_null" -p "guide_grp";
	rename -uid "A1303674-4E89-7B54-593A-338FE3CB1A6D";
	addAttr -ci true -sn "proxyEnableShake" -ln "proxyEnableShake" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableNoiseA" -ln "proxyEnableNoiseA" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedA" -ln "proxySeedA" -at "double";
	addAttr -ci true -sn "proxySpeedA" -ln "proxySpeedA" -at "double";
	addAttr -ci true -sn "proxyMagnitudeA" -ln "proxyMagnitudeA" -at "double";
	addAttr -ci true -sn "proxyEnableNoiseB" -ln "proxyEnableNoiseB" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedB" -ln "proxySeedB" -at "double";
	addAttr -ci true -sn "proxySpeedB" -ln "proxySpeedB" -at "double";
	addAttr -ci true -sn "proxyMagnitudeB" -ln "proxyMagnitudeB" -at "double";
	addAttr -ci true -sn "proxyEnableTX" -ln "proxyEnableTX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableTY" -ln "proxyEnableTY" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableTZ" -ln "proxyEnableTZ" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -k on ".proxyEnableShake";
	setAttr -k on ".proxyEnableNoiseA";
	setAttr -k on ".proxySeedA";
	setAttr -k on ".proxySpeedA";
	setAttr -k on ".proxyMagnitudeA";
	setAttr -k on ".proxyEnableNoiseB";
	setAttr -k on ".proxySeedB";
	setAttr -k on ".proxySpeedB";
	setAttr -k on ".proxyMagnitudeB";
	setAttr -k on ".proxyEnableTX";
	setAttr -k on ".proxyEnableTY";
	setAttr -k on ".proxyEnableTZ";
createNode transform -n "shakeFilm_null" -p "guide_grp";
	rename -uid "9DCBD0EC-4C4C-2034-1884-57BE9C3305A7";
	addAttr -ci true -sn "proxyEnableShake" -ln "proxyEnableShake" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableNoiseA" -ln "proxyEnableNoiseA" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedA" -ln "proxySeedA" -at "double";
	addAttr -ci true -sn "proxySpeedA" -ln "proxySpeedA" -at "double";
	addAttr -ci true -sn "proxyMagnitudeA" -ln "proxyMagnitudeA" -at "double";
	addAttr -ci true -sn "proxyEnableNoiseB" -ln "proxyEnableNoiseB" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxySeedB" -ln "proxySeedB" -at "double";
	addAttr -ci true -sn "proxySpeedB" -ln "proxySpeedB" -at "double";
	addAttr -ci true -sn "proxyMagnitudeB" -ln "proxyMagnitudeB" -at "double";
	addAttr -ci true -sn "proxyEnableTX" -ln "proxyEnableTX" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "proxyEnableTY" -ln "proxyEnableTY" -min 0 -max 1 -at "bool";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -k on ".proxyEnableShake";
	setAttr -k on ".proxyEnableNoiseA";
	setAttr -k on ".proxySeedA";
	setAttr -k on ".proxySpeedA";
	setAttr -k on ".proxyMagnitudeA";
	setAttr -k on ".proxyEnableNoiseB";
	setAttr -k on ".proxySeedB";
	setAttr -k on ".proxySpeedB";
	setAttr -k on ".proxyMagnitudeB";
	setAttr -k on ".proxyEnableTX";
	setAttr -k on ".proxyEnableTY";
createNode transform -n "gridGuide_C_crv" -p "guide_grp";
	rename -uid "D8BA04F2-4964-A333-B281-139E3BF3A04A";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".ovc" 1;
createNode nurbsCurve -n "gridGuide_C_crvShape" -p "gridGuide_C_crv";
	rename -uid "606AEAE2-4FC7-5320-6009-80A7DB1EBFF6";
	setAttr -k off ".v";
	setAttr ".ovp" no;
	setAttr ".cc" -type "nurbsCurve" 
		1 13 0 no 3
		14 0 1 2 3 4 5 6 7 8 9 10 11 12 13
		14
		-0.5 0.5 -8.3266726846886741e-17
		0.5 0.5 -8.3266726846886741e-17
		0.5 -0.5 8.3266726846886741e-17
		-0.5 -0.5 8.3266726846886741e-17
		-0.5 0.5 -8.3266726846886741e-17
		-0.1666666567325592 0.5 -8.3266726846886741e-17
		-0.1666666567325592 -0.5 8.3266726846886741e-17
		0.1666666716337204 -0.5 8.3266726846886741e-17
		0.16666668653488159 0.5 -8.3266726846886741e-17
		0.5 0.5 -8.3266726846886741e-17
		0.5 0.16666667163372034 -6.9388939039072284e-18
		-0.5 0.16666668653488159 0
		-0.5 -0.1666666567325592 6.9388939039072284e-18
		0.5 -0.1666666567325592 6.9388939039072284e-18
		;
createNode transform -n "frustum_C_crv" -p "guide_grp";
	rename -uid "CC58E9D3-404A-5DBF-BE68-B1ABB500371A";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
createNode nurbsCurve -n "frustum_C_crvShape" -p "frustum_C_crv";
	rename -uid "AA5D6AC2-4245-373A-0246-CCA22BBEA69B";
	setAttr -k off ".v";
	setAttr -s 2 ".cp";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		5.1428465843200684 2.8928513526916504 -10
		51.428466796875 28.92851638793945 -100
		;
createNode nurbsCurve -n "frustum_C_crvShape1" -p "frustum_C_crv";
	rename -uid "4ECD60BA-40C4-32AD-B808-82A31579827F";
	setAttr -k off ".v";
	setAttr -s 2 ".cp";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		5.1428465843200684 -2.8928513526916504 -10
		51.428466796875 -28.92851638793945 -100
		;
createNode nurbsCurve -n "frustum_C_crvShape2" -p "frustum_C_crv";
	rename -uid "330372EA-49C2-CD51-0776-34A9564B6AC7";
	setAttr -k off ".v";
	setAttr -s 2 ".cp";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-5.1428465843200684 -2.8928513526916504 -10
		-51.428466796875 -28.92851638793945 -100
		;
createNode nurbsCurve -n "frustum_C_crvShape3" -p "frustum_C_crv";
	rename -uid "17019B58-43F6-63D4-6AA1-19BE6D41E16E";
	setAttr -k off ".v";
	setAttr -s 2 ".cp";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		-5.1428465843200684 2.8928513526916504 -10
		-51.428466796875 28.92851638793945 -100
		;
createNode transform -n "filmOffsetSliderArea_crv" -p "guide_grp";
	rename -uid "54A5B115-40BA-8173-11BB-18B4C1307923";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".ovc" 1;
createNode nurbsCurve -n "filmOffsetSliderArea_crvShape" -p "filmOffsetSliderArea_crv";
	rename -uid "49D4AF5F-4D93-2F45-8F8A-17A2A7BD9635";
	setAttr -k off ".v";
	setAttr ".ls" 2;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 2 no 3
		5 0 1 2 3 4
		5
		3 3 -4.9960036108132044e-16
		3 -3 4.9960036108132044e-16
		-3 -3 4.9960036108132044e-16
		-3 3 -4.9960036108132044e-16
		3 3 -4.9960036108132044e-16
		;
createNode transform -n "filmOffsetSliderOffset_C_null" -p "filmOffsetSliderArea_crv";
	rename -uid "1545A2AA-410C-4008-7D37-F79E285C13D8";
	setAttr ".s" -type "double3" 5 5 5 ;
createNode transform -n "perspectiveGuide_null" -p "guide_grp";
	rename -uid "B9AF4C73-4CDE-598C-8FF2-AFA44A37CD06";
createNode transform -n "horizontalGuide_C_crv" -p "perspectiveGuide_null";
	rename -uid "6783756B-47A1-065B-2DCC-14864FD400F6";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".ovc" 1;
createNode nurbsCurve -n "horizontalGuide_C_crvShape" -p "horizontalGuide_C_crv";
	rename -uid "B0B34CC3-466B-E8FA-8FD8-ACB3E0DC0F36";
	setAttr -k off ".v";
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.70691619525397653 4.3286132789160339e-17 -0.70691619525397653
		6.1215836053113294e-17 6.1215836053113294e-17 -0.99973047078935884
		-0.70691619525397653 4.3286132789160339e-17 -0.70691619525397609
		-0.99973047078935906 3.1734397508999694e-33 1.618049084911016e-15
		-0.70691619525397653 -4.3286132789160339e-17 0.70691619525397653
		-1.0014368500594666e-16 -6.1215836053113344e-17 0.99973047078935928
		0.70691619525397653 -4.3286132789160339e-17 0.70691619525397609
		0.99973047078935906 -8.3479819486086627e-33 1.8062081803747911e-15
		0.70691619525397653 4.3286132789160339e-17 -0.70691619525397653
		6.1215836053113294e-17 6.1215836053113294e-17 -0.99973047078935884
		-0.70691619525397653 4.3286132789160339e-17 -0.70691619525397609
		;
createNode transform -n "verticalGuide_C_crv" -p "perspectiveGuide_null";
	rename -uid "DB21C369-4581-B0E6-87D3-E1BF768CBE77";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".ovc" 1;
createNode nurbsCurve -n "verticalGuide_C_crvShape" -p "verticalGuide_C_crv";
	rename -uid "BDED0F42-4FA8-8E55-A0D1-5E8DEE451DDD";
	setAttr -k off ".v";
	setAttr ".ls" 3;
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		2.5039018421923017e-17 -0.70691619525397609 -0.70691619525397653
		6.1215836053113344e-17 -6.1215836053113344e-17 -0.99973047078935884
		2.5039018421923017e-17 0.70691619525397653 -0.70691619525397609
		-5.0078036843846022e-17 0.99973047078935906 1.618049084911016e-15
		-2.5039018421923011e-17 0.70691619525397609 0.70691619525397653
		-6.1215836053113344e-17 1.0014368500594666e-16 0.99973047078935928
		-2.5039018421923011e-17 -0.70691619525397653 0.70691619525397609
		5.0078036843846035e-17 -0.99973047078935906 1.8062081803747911e-15
		2.5039018421923017e-17 -0.70691619525397609 -0.70691619525397653
		6.1215836053113344e-17 -6.1215836053113344e-17 -0.99973047078935884
		2.5039018421923017e-17 0.70691619525397653 -0.70691619525397609
		;
createNode decomposeMatrix -n "allRigTransform_dcpMtx";
	rename -uid "5E4BCF1D-4D01-CE1B-88BA-AFABF28CE7ED";
createNode blendMatrix -n "aimBlend_blendMtx";
	rename -uid "6C4D31A7-48AD-3D2C-C588-18A499C59D67";
	setAttr ".tgt[0].sca" no;
	setAttr ".tgt[0].tra" no;
	setAttr ".tgt[0].she" no;
createNode multMatrix -n "allRigMatrix_mulMtx";
	rename -uid "4CC07F0E-4D40-2211-9B87-DC9F86428403";
	setAttr -s 5 ".i";
createNode aimMatrix -n "cameraAim_aimMtx";
	rename -uid "6C879942-4D92-7E96-36C8-EB94ACA9AD5C";
	setAttr ".pmi" -type "double3" 0 0 -1 ;
	setAttr ".sm" 1;
createNode multMatrix -n "aimTarget_mulMtx";
	rename -uid "0679ABE9-485A-23B4-D8EE-1F843F9C38AA";
	setAttr -s 3 ".i";
createNode multMatrix -n "aimTargetOffset_mulMtx";
	rename -uid "7DBCAD5A-4909-3532-A835-D5A8BCC9FD26";
	setAttr -s 2 ".i";
createNode fourByFourMatrix -n "aimTargetOffset_4x4Mtx";
	rename -uid "65A14168-4215-F507-9199-0793CDB0D451";
	setAttr ".i32" -100;
createNode blendMatrix -n "aimParentSwitch_blendMtx";
	rename -uid "B4F33651-443F-A1B1-B6C8-A085F1E214DE";
	setAttr -s 4 ".tgt";
createNode condition -n "allRig_condition";
	rename -uid "82D3F2E3-4E11-B888-27AF-E6842DF18558";
	setAttr ".ct" -type "float3" 1 1 1 ;
	setAttr ".cf" -type "float3" 0 0 0 ;
createNode multMatrix -n "aimParentA_mulMtx";
	rename -uid "C6A4A1D7-45B6-6538-AE3D-39966133E9E9";
	setAttr -s 3 ".i";
createNode condition -n "aimParentA_condition";
	rename -uid "CC38D4B6-4902-3B73-2F66-15B8850F1781";
	setAttr ".st" 1;
	setAttr ".ct" -type "float3" 1 1 1 ;
	setAttr ".cf" -type "float3" 0 0 0 ;
createNode multMatrix -n "aimParentB_mulMtx";
	rename -uid "3AD5A788-44E2-421C-9687-CDA5AAE1B01D";
	setAttr -s 2 ".i";
createNode condition -n "aimParentB_condition";
	rename -uid "F15CB71B-437B-9CF9-CC06-9A9FCD3C96DB";
	setAttr ".st" 2;
	setAttr ".ct" -type "float3" 1 1 1 ;
	setAttr ".cf" -type "float3" 0 0 0 ;
createNode multMatrix -n "aimParentC_mulMtx";
	rename -uid "34E5C79F-4CA1-6850-DBB2-F19CF37671C2";
createNode condition -n "aimParentC_condition";
	rename -uid "9861AF8E-482D-1EF8-89A1-FABFDF4D927C";
	setAttr ".st" 3;
	setAttr ".ct" -type "float3" 1 1 1 ;
	setAttr ".cf" -type "float3" 0 0 0 ;
createNode multMatrix -n "aimUpTarget_mulMtx";
	rename -uid "B6A0C864-4D66-B3F2-AD9E-FEA459FE6413";
	setAttr -s 2 ".i";
createNode plusMinusAverage -n "filmOffset_add";
	rename -uid "4E72E5CB-4808-E044-E1DE-F8932634325A";
	setAttr -s 2 ".i2";
	setAttr -s 2 ".i2";
createNode multiplyDivide -n "locatorScale_mul";
	rename -uid "03FE72A2-4898-859F-FD04-F4B1F64493FC";
	setAttr ".i2" -type "float3" 5 1 1 ;
createNode transformGeometry -n "root_C_ctrlShape_tg";
	rename -uid "7E1FE3C2-4C25-3A8B-48C5-8BBD8D83DAE0";
createNode composeMatrix -n "rigSize_cmpMtx";
	rename -uid "16F00B92-47ED-A819-BB82-95888A195EA0";
createNode transformGeometry -n "local_C_ctrlShape_tg";
	rename -uid "5727ABC5-4495-1066-CB20-E4A9CB1D3AA9";
createNode transformGeometry -n "body_C_ctrlShape_tg";
	rename -uid "C02BFD56-4904-EE2C-03E9-8EB9A6487EF7";
createNode transformGeometry -n "camera_C_ctrlShape_tg";
	rename -uid "728C2821-413B-8A93-D3B8-F2910F6668D2";
createNode transformGeometry -n "camera_C_ctrl1Shape_tg";
	rename -uid "B6D31BAF-4A43-5883-F6D1-DB84C61DAA96";
createNode multMatrix -n "filmOffsetSlider_mulMtx";
	rename -uid "ECF35ACF-4FE7-4C70-F79A-9ABA4950F0E1";
	setAttr -s 2 ".i";
createNode multMatrix -n "filmOffsetSliderAreaOffset_mulMtx";
	rename -uid "7B62C770-448D-5102-7E61-1FB2AFB5A474";
	setAttr -s 3 ".i";
createNode fourByFourMatrix -n "filmOffsetSliderOffset_4x4Mtx";
	rename -uid "5B2300D7-465B-E050-4C34-98A2933FEAEF";
	setAttr ".i31" 10;
createNode transformGeometry -n "aimTarget_C_ctrlShape_tg";
	rename -uid "0DC96562-44EC-CA38-EC80-FE801240E4AC";
createNode transformGeometry -n "aimTarget_C_ctrlShape1_tg";
	rename -uid "8B40B147-48C9-23AB-9B95-A8A8DBD6A5A9";
createNode transformGeometry -n "aimTarget_C_ctrlShape2_tg";
	rename -uid "DD114A35-4708-4E84-05D8-8494B82D3504";
createNode multMatrix -n "nearClipPlaneOffset_mulMtx";
	rename -uid "A00365BD-40C6-4B62-D1A9-91B95F428266";
	setAttr -s 3 ".i";
createNode composeMatrix -n "nearClipPlaneOffset_cmpMtx";
	rename -uid "E7054E91-4238-2A32-01F3-CF8975AB2DFF";
createNode multiplyDivide -n "nearFilmOffset_mul";
	rename -uid "B2C9C3B8-4300-B94E-A456-1FBA04B85667";
createNode multiplyDivide -n "nearDistanceScale_mul";
	rename -uid "BFD45690-45E1-7087-6248-0B8DD660FBED";
createNode multiplyDivide -n "apertureRate_div";
	rename -uid "B3ADDF1C-4564-59C6-13E7-B2BCBC702953";
	setAttr ".op" 2;
createNode multiplyDivide -n "aperture_mul";
	rename -uid "96AE9DEB-4EE1-0D57-10DF-FDA5508A64B5";
	setAttr ".i2" -type "float3" 25.4 25.4 1 ;
createNode multiplyDivide -n "filmOffsetRate_mul";
	rename -uid "E1CB41BB-468E-CFFE-E301-0695591B6BB9";
	setAttr ".op" 2;
createNode multiplyDivide -n "nearFitResolutionGate_mul";
	rename -uid "E2208C17-45A9-9C0E-AB2D-FE97928AEC4C";
createNode multiplyDivide -n "horizontaResolutionGateRatio_div";
	rename -uid "F8F89F0B-4CC9-B6C0-6B39-A582EB1FF1BA";
	setAttr ".op" 2;
createNode multiplyDivide -n "filmAspectRatio_div";
	rename -uid "96E40860-41FC-B8E2-166E-EE9066539076";
	setAttr ".op" 2;
createNode fourByFourMatrix -n "clippingOffset_4x4Mtx";
	rename -uid "2EE32922-4F1F-90CE-7490-03879DBAA0B3";
	setAttr ".i22" -1;
createNode multMatrix -n "farClipPlaneOffset_mulMtx";
	rename -uid "0166B84D-4764-FAE8-5A06-77BE7B7CABB6";
	setAttr -s 3 ".i";
createNode composeMatrix -n "farClipPlaneOffset_cmpMtx";
	rename -uid "420E7ECD-423A-E9D9-BB3F-A9B63B179A2F";
createNode multiplyDivide -n "farFilmOffset_mul";
	rename -uid "E543B1A5-460B-B60C-69C1-4BA8AA4D0276";
createNode multiplyDivide -n "farDistanceScale_mul";
	rename -uid "FC087DEC-468B-E007-BBF8-62A51D8EE9AF";
createNode multiplyDivide -n "farFitResolutionGate_mul";
	rename -uid "AA21DA81-4879-C0D3-D149-6892A70F39A9";
createNode multMatrix -n "settingSpacer_mulMtx";
	rename -uid "8ED3E66E-439E-BC36-C63C-22AB7CE1AEFD";
	setAttr -s 2 ".i";
createNode multMatrix -n "aimUpTargetOffset_mulMtx";
	rename -uid "96CECCD2-4FB1-76FA-0402-739AE85C2046";
	setAttr -s 3 ".i";
createNode fourByFourMatrix -n "aimUpTargetOffset_4x4Mtx";
	rename -uid "EBBA6C4F-4C7B-1175-D20F-B28FEC845C16";
	setAttr ".i31" 50;
createNode composeMatrix -n "aimUpTargetRoll_cmpMtx";
	rename -uid "4FDF1105-4E8E-FDB2-AE4A-2580B4A45402";
createNode unitConversion -n "unitConversion6";
	rename -uid "FF2A395E-42CB-718A-214A-9A82FE9E26B1";
	setAttr ".cf" 0.017453292519943295;
createNode expression -n "cameraNoise_exp";
	rename -uid "63057298-4EBF-B7B6-AD4E-FDBF9CB67597";
	setAttr -k on ".nds";
	setAttr -s 23 ".in";
	setAttr -s 23 ".in";
	setAttr -s 6 ".out";
	setAttr ".ixp" -type "string" (
		"if(.I[0] == true){\n\t// Noise A\n\tfloat $txA = 0.0;\n\tfloat $tyA = 0.0;\n\tfloat $tzA = 0.0;\n\tif(.I[1] == true){\n\t\t$txA = noise(.I[2] + (time * .I[3])) * .I[4];\n\t\t$tyA = noise(.I[2] + ((time + 1) * .I[3])) * .I[4];\n\t\t$tzA = noise(.I[2] + ((time + 2) * .I[3])) * .I[4];\n\t}\n\n\t// Noise B\n\tfloat $txB = 0.0;\n\tfloat $tyB = 0.0;\n\tfloat $tzB = 0.0;\n\tif(.I[5] == true){\n\t\t$txB = noise(.I[6] + ((time + 3) * .I[7])) * .I[8];\n\t\t$tyB = noise(.I[6] + ((time + 4) * .I[7])) * .I[8];\n\t\t$tzB = noise(.I[6] + ((time + 5) * .I[7])) * .I[8];\n\t}\n\n\t// Noise C\n\tfloat $rxA = 0.0;\n\tfloat $ryA = 0.0;\n\tfloat $rzA = 0.0;\n\tif(.I[9] == true){\n\t\t$rxA = noise(.I[10] + ((time + 6) * .I[11])) * .I[12];\n\t\t$ryA = noise(.I[10] + ((time + 7) * .I[11])) * .I[12];\n\t\t$rzA = noise(.I[10] + ((time + 8) * .I[11])) * .I[12];\n\t}\n\n\t// Noise D\n\tfloat $rxB = 0.0;\n\tfloat $ryB = 0.0;\n\tfloat $rzB = 0.0;\n\tif(.I[13] == true){\n\t\t$rxB = noise(.I[14] + ((time + 9) * .I[15])) * .I[16];\n\t\t$ryB = noise(.I[14] + ((time + 10) * .I[15])) * .I[16];\n\t\t$rzB = noise(.I[14] + ((time + 11) * .I[15])) * .I[16];\n"
		+ "\t}\n\n\t// Apply noise\n\t.O[0] = ($txA + $txB) * .I[17];\n\t.O[1] = ($tyA + $tyB) * .I[18];\n\t.O[2] = ($tzA + $tzB) * .I[19];\n\t.O[3] = ($rxA + $rxB)  * .I[20];\n\t.O[4] = ($ryA + $ryB)  * .I[21];\n\t.O[5] = ($rzA + $rzB)  * .I[22];\n\n}else{\n\t.O[0] = 0;\n\t.O[1] = 0;\n\t.O[2] = 0;\n\t.O[3] = 0;\n\t.O[4] = 0;\n\t.O[5] = 0;\n}");
createNode unitConversion -n "unitConversion3";
	rename -uid "C04B6D29-43CF-D3DB-AF80-359EB2932969";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion4";
	rename -uid "8D9224C5-4DAF-9EF2-B089-9B8BD529208E";
	setAttr ".cf" 0.017453292519943295;
createNode unitConversion -n "unitConversion5";
	rename -uid "4A3EC36C-4CF5-C317-1149-F4A203271A06";
	setAttr ".cf" 0.017453292519943295;
createNode expression -n "aimTargetNoise_exp";
	rename -uid "3F3AC2F5-4C06-C05F-CDE6-B1A8325A38B1";
	setAttr -k on ".nds";
	setAttr -s 22 ".in[12:21]"  1 1000 2 5 1 1 0 1 1 0;
	setAttr -s 12 ".in";
	setAttr -s 3 ".out";
	setAttr ".ixp" -type "string" "if(.I[0] == true){\n\t// Noise A\n\tfloat $txA = 0.0;\n\tfloat $tyA = 0.0;\n\tfloat $tzA = 0.0;\n\tif(.I[1] == true){\n\t\t$txA = noise(.I[2] + (time * .I[3])) * .I[4];\n\t\t$tyA = noise(.I[2] + ((time + 1) * .I[3])) * .I[4];\n\t\t$tzA = noise(.I[2] + ((time + 2) * .I[3])) * .I[4];\n\t}\n\n\t// Noise B\n\tfloat $txB = 0.0;\n\tfloat $tyB = 0.0;\n\tfloat $tzB = 0.0;\n\tif(.I[5] == true){\n\t\t$txB = noise(.I[6] + ((time + 3) * .I[7])) * .I[8];\n\t\t$tyB = noise(.I[6] + ((time + 4) * .I[7])) * .I[8];\n\t\t$tzB = noise(.I[6] + ((time + 5) * .I[7])) * .I[8];\n\t}\n\n\n\t// Apply noise\n\t.O[0] = ($txA + $txB) * .I[9];\n\t.O[1] = ($tyA + $tyB) * .I[10];\n\t.O[2] = ($tzA + $tzB) * .I[11];\n\n}else{\n\t.O[0] = 0;\n\t.O[1] = 0;\n\t.O[2] = 0;\n}";
createNode expression -n "expression1";
	rename -uid "C41B5948-402E-DB97-8D4D-02B22CE0FB87";
	setAttr -k on ".nds";
	setAttr -s 11 ".in";
	setAttr -s 11 ".in";
	setAttr -s 2 ".out";
	setAttr ".ixp" -type "string" "if(.I[0] == true){\n\t// Noise A\n\tfloat $txA = 0.0;\n\tfloat $tyA = 0.0;\n\tif(.I[1] == true){\n\t\t$txA = noise(.I[2] + time * .I[3]) * .I[4];\n\t\t$tyA = noise(.I[2] + time * .I[3] + 1) * .I[4];\n\t}\n\n\t// Noise B\n\tfloat $txB = 0.0;\n\tfloat $tyB = 0.0;\n\tif(.I[5] == true){\n\t\t$txB = noise(.I[6] + time * .I[7] + 2) * .I[8];\n\t\t$tyB = noise(.I[6] + time * .I[7] + 3) * .I[8];\n\t}\n\n\n\t// Apply noise\n\t.O[0] = ($txA + $txB) * .I[9];\n\t.O[1] = ($tyA + $tyB) * .I[10];\n\n}else{\n\t.O[0] = 0;\n\t.O[1] = 0;\n}";
createNode multMatrix -n "gridGuideOffset_mulMtx";
	rename -uid "A9991059-468C-A0D5-7457-E4B58EBB53D3";
	setAttr -s 2 ".i";
createNode pointOnCurveInfo -n "frustumAA_pointInfo";
	rename -uid "EB5FA463-4B5B-7E56-91BC-0CBD80CE1F59";
createNode pointOnCurveInfo -n "frustumAB_pointInfo";
	rename -uid "D3FF09FE-47ED-8068-1081-739CC8A7A8A4";
createNode pointOnCurveInfo -n "frustumBA_pointInfo";
	rename -uid "43E39E79-40E1-617A-F240-9CA7938CBB07";
	setAttr ".pr" 1;
createNode pointOnCurveInfo -n "frustumBB_pointInfo";
	rename -uid "81A89DC9-43C4-12E0-DCD7-37BFFBDD665D";
	setAttr ".pr" 1;
createNode pointOnCurveInfo -n "frustumCA_pointInfo";
	rename -uid "0FCB022B-4B17-0701-BA7B-7E99707C15D6";
	setAttr ".pr" 2;
createNode pointOnCurveInfo -n "frustumCB_pointInfo";
	rename -uid "EA142AA6-4B3D-9257-EF49-D8ADC6C8A046";
	setAttr ".pr" 2;
createNode pointOnCurveInfo -n "frustumDA_pointInfo";
	rename -uid "D2297F23-4F39-CA02-394C-E2B8EB0B1494";
	setAttr ".pr" 3;
createNode pointOnCurveInfo -n "frustumDB_pointInfo";
	rename -uid "9E44E45D-4CDB-356A-8CED-F49928B4F84B";
	setAttr ".pr" 3;
createNode multiplyDivide -n "nearClipPlaneBoost_mul";
	rename -uid "3A65110C-4244-133E-D962-1DA86312377B";
	setAttr ".i2" -type "float3" 0.5 0.5 0.5 ;
createNode addDoubleLinear -n "nearFarClipPlane_add";
	rename -uid "90A62642-437C-ABDE-5AD0-608DFB353ACD";
	setAttr ".ihi" 2;
createNode unitConversion -n "unitConversion1";
	rename -uid "40899AA3-42A6-93EF-931C-3EB1075F6252";
	setAttr ".cf" 0.017453292519943295;
select -ne :time1;
	setAttr -av -k on ".cch";
	setAttr -av -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".o" 69;
	setAttr -av ".unw" 69;
	setAttr -k on ".etw";
	setAttr -k on ".tps";
	setAttr -av -k on ".tms";
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".st";
	setAttr -cb on ".an";
	setAttr -cb on ".pt";
select -ne :renderGlobalsList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :defaultShaderList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 5 ".s";
select -ne :postProcessList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".p";
select -ne :defaultRenderUtilityList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 39 ".u";
select -ne :defaultRenderingList1;
select -ne :initialShadingGroup;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".mwc";
	setAttr -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr -k on ".ro" yes;
select -ne :initialParticleSE;
	setAttr -av -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".mwc";
	setAttr -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr -k on ".ro" yes;
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr ".ren" -type "string" "arnold";
	setAttr ".outf" 51;
	setAttr ".imfkey" -type "string" "exr";
	setAttr ".dss" -type "string" "lambert1";
select -ne :defaultResolution;
	setAttr -av -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -k on ".bnm";
	setAttr -av -k on ".w";
	setAttr -av -k on ".h";
	setAttr -av -k on ".pa" 1;
	setAttr -av -k on ".al";
	setAttr -k on ".dar" 1.7777777910232544;
	setAttr -av -k on ".ldar";
	setAttr -cb on ".dpi";
	setAttr -av -k on ".off";
	setAttr -av -k on ".fld";
	setAttr -av -k on ".zsl";
	setAttr -cb on ".isu";
	setAttr -cb on ".pdu";
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "<MAYA_RESOURCES>/OCIO-configs/Maya2022-default/config.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".vn" -type "string" "ACES 1.0 SDR-video";
	setAttr ".dn" -type "string" "sRGB";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".potn" -type "string" "ACES 1.0 SDR-video (sRGB)";
select -ne :hardwareRenderGlobals;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr ".ctrs" 256;
	setAttr -av ".btrs" 512;
	setAttr -k off ".fbfm";
	setAttr -k off -cb on ".ehql";
	setAttr -k off -cb on ".eams";
	setAttr -k off -cb on ".eeaa";
	setAttr -k off -cb on ".engm";
	setAttr -k off -cb on ".mes";
	setAttr -k off -cb on ".emb";
	setAttr -av -k off -cb on ".mbbf";
	setAttr -k off -cb on ".mbs";
	setAttr -k off -cb on ".trm";
	setAttr -k off -cb on ".tshc";
	setAttr -k off ".enpt";
	setAttr -k off -cb on ".clmt";
	setAttr -k off -cb on ".tcov";
	setAttr -k off -cb on ".lith";
	setAttr -k off -cb on ".sobc";
	setAttr -k off -cb on ".cuth";
	setAttr -k off -cb on ".hgcd";
	setAttr -k off -cb on ".hgci";
	setAttr -k off -cb on ".mgcs";
	setAttr -k off -cb on ".twa";
	setAttr -k off -cb on ".twz";
	setAttr -k on ".hwcc";
	setAttr -k on ".hwdp";
	setAttr -k on ".hwql";
	setAttr -k on ".hwfr";
	setAttr -k on ".soll";
	setAttr -k on ".sosl";
	setAttr -k on ".bswa";
	setAttr -k on ".shml";
	setAttr -k on ".hwel";
connectAttr "allRigTransform_dcpMtx.ot" "render_cam.t";
connectAttr "allRigTransform_dcpMtx.or" "render_cam.r";
connectAttr "allRigTransform_dcpMtx.os" "render_cam.s";
connectAttr "allRigTransform_dcpMtx.osh" "render_cam.sh";
connectAttr "camera_C_ctrl.focalLength" "render_camShape.fl";
connectAttr "nearClipPlane_C_ctrl.tz" "render_camShape.ncp";
connectAttr "filmOffset_add.o2x" "render_camShape.hfo";
connectAttr "filmOffset_add.o2y" "render_camShape.vfo";
connectAttr "farClipPlane_C_ctrl.tz" "render_camShape.fcp";
connectAttr "settings_C_ctrl.gateOpacity" "render_camShape.dgo";
connectAttr "locatorScale_mul.ox" "render_camShape.lls";
connectAttr "settings_C_ctrl.hideRigOnPlayblack" "controller_grp.hpb";
connectAttr "root_C_ctrlShape_tg.og" "root_C_ctrlShape.cr";
connectAttr "local_C_ctrlShape_tg.og" "local_C_ctrlShape.cr";
connectAttr "body_C_ctrlShape_tg.og" "body_C_ctrlShape.cr";
connectAttr "camera_C_ctrlShape_tg.og" "camera_C_ctrlShape.cr";
connectAttr "camera_C_ctrl1Shape_tg.og" "camera_C_ctrlShape1.cr";
connectAttr "filmOffsetSlider_mulMtx.o" "filmOffsetSlider_C_ctrl.opm";
connectAttr "aimTargetOffset_mulMtx.o" "aimTarget_C_ctrl.opm";
connectAttr "aimTarget_C_ctrlShape_tg.og" "aimTarget_C_ctrlShape.cr";
connectAttr "aimTarget_C_ctrlShape1_tg.og" "aimTarget_C_ctrlShape1.cr";
connectAttr "aimTarget_C_ctrlShape2_tg.og" "aimTarget_C_ctrlShape2.cr";
connectAttr "nearClipPlaneOffset_mulMtx.o" "nearClipPlane_C_ctrl.opm";
connectAttr "farClipPlaneOffset_mulMtx.o" "farClipPlane_C_ctrl.opm";
connectAttr "settingSpacer_mulMtx.o" "settings_C_ctrl.opm";
connectAttr "settings_C_ctrl.hideGuideOnPlayblack" "guide_grp.hpb";
connectAttr "aimUpTargetOffset_mulMtx.o" "aimUpTarget_C_null.opm";
connectAttr "camera_C_ctrl.enableShake" "shakeCamera_null.proxyEnableShake";
connectAttr "camera_C_ctrl.enableNoiseA" "shakeCamera_null.proxyEnableNoiseA";
connectAttr "camera_C_ctrl.seedA" "shakeCamera_null.proxySeedA";
connectAttr "camera_C_ctrl.speedA" "shakeCamera_null.proxySpeedA";
connectAttr "camera_C_ctrl.magnitudeA" "shakeCamera_null.proxyMagnitudeA";
connectAttr "camera_C_ctrl.enableNoiseB" "shakeCamera_null.proxyEnableNoiseB";
connectAttr "camera_C_ctrl.seedB" "shakeCamera_null.proxySeedB";
connectAttr "camera_C_ctrl.speedB" "shakeCamera_null.proxySpeedB";
connectAttr "camera_C_ctrl.magnitudeB" "shakeCamera_null.proxyMagnitudeB";
connectAttr "camera_C_ctrl.enableNoiseC" "shakeCamera_null.proxyEnableNoiseC";
connectAttr "camera_C_ctrl.seedC" "shakeCamera_null.proxySeedC";
connectAttr "camera_C_ctrl.speedC" "shakeCamera_null.proxySpeedC";
connectAttr "camera_C_ctrl.magnitudeC" "shakeCamera_null.proxyMagnitudeC";
connectAttr "camera_C_ctrl.enableNoiseD" "shakeCamera_null.proxyEnableNoiseD";
connectAttr "camera_C_ctrl.seedD" "shakeCamera_null.proxySeedD";
connectAttr "camera_C_ctrl.speedD" "shakeCamera_null.proxySpeedD";
connectAttr "camera_C_ctrl.magnitudeD" "shakeCamera_null.proxyMagnitudeD";
connectAttr "camera_C_ctrl.enableTX" "shakeCamera_null.proxyEnableTX";
connectAttr "camera_C_ctrl.enableTY" "shakeCamera_null.proxyEnableTY";
connectAttr "camera_C_ctrl.enableTZ" "shakeCamera_null.proxyEnableTZ";
connectAttr "camera_C_ctrl.enableRX" "shakeCamera_null.proxyEnableRX";
connectAttr "camera_C_ctrl.enableRY" "shakeCamera_null.proxyEnableRY";
connectAttr "camera_C_ctrl.enableRZ" "shakeCamera_null.proxyEnableRZ";
connectAttr "cameraNoise_exp.out[0]" "shakeCamera_null.tx";
connectAttr "cameraNoise_exp.out[1]" "shakeCamera_null.ty";
connectAttr "cameraNoise_exp.out[2]" "shakeCamera_null.tz";
connectAttr "unitConversion3.o" "shakeCamera_null.rx";
connectAttr "unitConversion4.o" "shakeCamera_null.ry";
connectAttr "unitConversion5.o" "shakeCamera_null.rz";
connectAttr "aimTarget_C_ctrl.enableShake" "shakeAimTarget_null.proxyEnableShake"
		;
connectAttr "aimTarget_C_ctrl.enableNoiseA" "shakeAimTarget_null.proxyEnableNoiseA"
		;
connectAttr "aimTarget_C_ctrl.seedA" "shakeAimTarget_null.proxySeedA";
connectAttr "aimTarget_C_ctrl.speedA" "shakeAimTarget_null.proxySpeedA";
connectAttr "aimTarget_C_ctrl.magnitudeA" "shakeAimTarget_null.proxyMagnitudeA";
connectAttr "aimTarget_C_ctrl.enableNoiseB" "shakeAimTarget_null.proxyEnableNoiseB"
		;
connectAttr "aimTarget_C_ctrl.seedB" "shakeAimTarget_null.proxySeedB";
connectAttr "aimTarget_C_ctrl.speedB" "shakeAimTarget_null.proxySpeedB";
connectAttr "aimTarget_C_ctrl.magnitudeB" "shakeAimTarget_null.proxyMagnitudeB";
connectAttr "aimTarget_C_ctrl.enableTX" "shakeAimTarget_null.proxyEnableTX";
connectAttr "aimTarget_C_ctrl.enableTY" "shakeAimTarget_null.proxyEnableTY";
connectAttr "aimTarget_C_ctrl.enableTZ" "shakeAimTarget_null.proxyEnableTZ";
connectAttr "aimTargetNoise_exp.out[0]" "shakeAimTarget_null.tx";
connectAttr "aimTargetNoise_exp.out[1]" "shakeAimTarget_null.ty";
connectAttr "aimTargetNoise_exp.out[2]" "shakeAimTarget_null.tz";
connectAttr "expression1.out[0]" "shakeFilm_null.tx";
connectAttr "expression1.out[1]" "shakeFilm_null.ty";
connectAttr "filmOffsetSlider_C_ctrl.enableShake" "shakeFilm_null.proxyEnableShake"
		;
connectAttr "filmOffsetSlider_C_ctrl.enableNoiseA" "shakeFilm_null.proxyEnableNoiseA"
		;
connectAttr "filmOffsetSlider_C_ctrl.seedA" "shakeFilm_null.proxySeedA";
connectAttr "filmOffsetSlider_C_ctrl.speedA" "shakeFilm_null.proxySpeedA";
connectAttr "filmOffsetSlider_C_ctrl.magnitudeA" "shakeFilm_null.proxyMagnitudeA"
		;
connectAttr "filmOffsetSlider_C_ctrl.enableNoiseB" "shakeFilm_null.proxyEnableNoiseB"
		;
connectAttr "filmOffsetSlider_C_ctrl.seedB" "shakeFilm_null.proxySeedB";
connectAttr "filmOffsetSlider_C_ctrl.speedB" "shakeFilm_null.proxySpeedB";
connectAttr "filmOffsetSlider_C_ctrl.magnitudeB" "shakeFilm_null.proxyMagnitudeB"
		;
connectAttr "filmOffsetSlider_C_ctrl.enableTX" "shakeFilm_null.proxyEnableTX";
connectAttr "filmOffsetSlider_C_ctrl.enableTY" "shakeFilm_null.proxyEnableTY";
connectAttr "settings_C_ctrl.gridGuide" "gridGuide_C_crv.v";
connectAttr "gridGuideOffset_mulMtx.o" "gridGuide_C_crv.opm";
connectAttr "frustumAA_pointInfo.p" "frustum_C_crvShape.cp[0]";
connectAttr "frustumAB_pointInfo.p" "frustum_C_crvShape.cp[1]";
connectAttr "frustumBA_pointInfo.p" "frustum_C_crvShape1.cp[0]";
connectAttr "frustumBB_pointInfo.p" "frustum_C_crvShape1.cp[1]";
connectAttr "frustumCA_pointInfo.p" "frustum_C_crvShape2.cp[0]";
connectAttr "frustumCB_pointInfo.p" "frustum_C_crvShape2.cp[1]";
connectAttr "frustumDA_pointInfo.p" "frustum_C_crvShape3.cp[0]";
connectAttr "frustumDB_pointInfo.p" "frustum_C_crvShape3.cp[1]";
connectAttr "filmOffsetSliderAreaOffset_mulMtx.o" "filmOffsetSliderArea_crv.opm"
		;
connectAttr "settings_C_ctrl.perspectiveGuide" "perspectiveGuide_null.v";
connectAttr "allRigTransform_dcpMtx.ot" "perspectiveGuide_null.t";
connectAttr "nearClipPlaneBoost_mul.o" "horizontalGuide_C_crv.s";
connectAttr "unitConversion1.o" "verticalGuide_C_crv.ry";
connectAttr "nearClipPlaneBoost_mul.o" "verticalGuide_C_crv.s";
connectAttr "aimBlend_blendMtx.omat" "allRigTransform_dcpMtx.imat";
connectAttr "allRigMatrix_mulMtx.o" "aimBlend_blendMtx.imat";
connectAttr "cameraAim_aimMtx.tmat" "aimBlend_blendMtx.tgt[0].tmat";
connectAttr "aimTarget_C_ctrl.aim" "aimBlend_blendMtx.tgt[0].wgt";
connectAttr "shakeCamera_null.m" "allRigMatrix_mulMtx.i[0]";
connectAttr "camera_C_ctrl.m" "allRigMatrix_mulMtx.i[1]";
connectAttr "body_C_ctrl.m" "allRigMatrix_mulMtx.i[2]";
connectAttr "local_C_ctrl.m" "allRigMatrix_mulMtx.i[3]";
connectAttr "root_C_ctrl.m" "allRigMatrix_mulMtx.i[4]";
connectAttr "aimTarget_mulMtx.o" "cameraAim_aimMtx.pmat";
connectAttr "aimUpTarget_mulMtx.o" "cameraAim_aimMtx.smat";
connectAttr "allRigMatrix_mulMtx.o" "cameraAim_aimMtx.imat";
connectAttr "shakeAimTarget_null.m" "aimTarget_mulMtx.i[0]";
connectAttr "aimTarget_C_ctrl.m" "aimTarget_mulMtx.i[1]";
connectAttr "aimTargetOffset_mulMtx.o" "aimTarget_mulMtx.i[2]";
connectAttr "aimTargetOffset_4x4Mtx.o" "aimTargetOffset_mulMtx.i[0]";
connectAttr "aimParentSwitch_blendMtx.omat" "aimTargetOffset_mulMtx.i[1]";
connectAttr "allRigMatrix_mulMtx.o" "aimParentSwitch_blendMtx.tgt[0].tmat";
connectAttr "allRig_condition.ocr" "aimParentSwitch_blendMtx.tgt[0].wgt";
connectAttr "aimParentA_mulMtx.o" "aimParentSwitch_blendMtx.tgt[1].tmat";
connectAttr "aimParentA_condition.ocr" "aimParentSwitch_blendMtx.tgt[1].wgt";
connectAttr "aimParentB_mulMtx.o" "aimParentSwitch_blendMtx.tgt[2].tmat";
connectAttr "aimParentB_condition.ocr" "aimParentSwitch_blendMtx.tgt[2].wgt";
connectAttr "aimParentC_mulMtx.o" "aimParentSwitch_blendMtx.tgt[3].tmat";
connectAttr "aimParentC_condition.ocr" "aimParentSwitch_blendMtx.tgt[3].wgt";
connectAttr "aimTarget_C_ctrl.parent" "allRig_condition.ft";
connectAttr "body_C_ctrl.m" "aimParentA_mulMtx.i[0]";
connectAttr "local_C_ctrl.m" "aimParentA_mulMtx.i[1]";
connectAttr "root_C_ctrl.m" "aimParentA_mulMtx.i[2]";
connectAttr "aimTarget_C_ctrl.parent" "aimParentA_condition.ft";
connectAttr "local_C_ctrl.m" "aimParentB_mulMtx.i[0]";
connectAttr "root_C_ctrl.m" "aimParentB_mulMtx.i[1]";
connectAttr "aimTarget_C_ctrl.parent" "aimParentB_condition.ft";
connectAttr "root_C_ctrl.m" "aimParentC_mulMtx.i[0]";
connectAttr "aimTarget_C_ctrl.parent" "aimParentC_condition.ft";
connectAttr "aimUpTarget_C_null.m" "aimUpTarget_mulMtx.i[0]";
connectAttr "aimUpTarget_C_null.opm" "aimUpTarget_mulMtx.i[1]";
connectAttr "filmOffsetSlider_C_ctrl.tx" "filmOffset_add.i2[0].i2x";
connectAttr "filmOffsetSlider_C_ctrl.ty" "filmOffset_add.i2[0].i2y";
connectAttr "shakeFilm_null.tx" "filmOffset_add.i2[1].i2x";
connectAttr "shakeFilm_null.ty" "filmOffset_add.i2[1].i2y";
connectAttr "settings_C_ctrl.rigSize" "locatorScale_mul.i1x";
connectAttr "rigSize_cmpMtx.omat" "root_C_ctrlShape_tg.txf";
connectAttr "root_C_ctrlShapeOrg.l" "root_C_ctrlShape_tg.ig";
connectAttr "settings_C_ctrl.rigSize" "rigSize_cmpMtx.isx";
connectAttr "settings_C_ctrl.rigSize" "rigSize_cmpMtx.isy";
connectAttr "settings_C_ctrl.rigSize" "rigSize_cmpMtx.isz";
connectAttr "rigSize_cmpMtx.omat" "local_C_ctrlShape_tg.txf";
connectAttr "local_C_ctrlShapeOrg.l" "local_C_ctrlShape_tg.ig";
connectAttr "rigSize_cmpMtx.omat" "body_C_ctrlShape_tg.txf";
connectAttr "body_C_ctrlShapeOrg.l" "body_C_ctrlShape_tg.ig";
connectAttr "rigSize_cmpMtx.omat" "camera_C_ctrlShape_tg.txf";
connectAttr "camera_C_ctrlShapeOrg.l" "camera_C_ctrlShape_tg.ig";
connectAttr "rigSize_cmpMtx.omat" "camera_C_ctrl1Shape_tg.txf";
connectAttr "camera_C_ctrlShape1Org.l" "camera_C_ctrl1Shape_tg.ig";
connectAttr "filmOffsetSliderOffset_C_null.m" "filmOffsetSlider_mulMtx.i[0]";
connectAttr "filmOffsetSliderAreaOffset_mulMtx.o" "filmOffsetSlider_mulMtx.i[1]"
		;
connectAttr "filmOffsetSliderOffset_4x4Mtx.o" "filmOffsetSliderAreaOffset_mulMtx.i[0]"
		;
connectAttr "rigSize_cmpMtx.omat" "filmOffsetSliderAreaOffset_mulMtx.i[1]";
connectAttr "aimBlend_blendMtx.omat" "filmOffsetSliderAreaOffset_mulMtx.i[2]";
connectAttr "rigSize_cmpMtx.omat" "aimTarget_C_ctrlShape_tg.txf";
connectAttr "aimTarget_C_ctrlShapeOrg.l" "aimTarget_C_ctrlShape_tg.ig";
connectAttr "rigSize_cmpMtx.omat" "aimTarget_C_ctrlShape1_tg.txf";
connectAttr "aimTarget_C_ctrlShape1Org.l" "aimTarget_C_ctrlShape1_tg.ig";
connectAttr "rigSize_cmpMtx.omat" "aimTarget_C_ctrlShape2_tg.txf";
connectAttr "aimTarget_C_ctrlShape2Org.l" "aimTarget_C_ctrlShape2_tg.ig";
connectAttr "nearClipPlaneOffset_cmpMtx.omat" "nearClipPlaneOffset_mulMtx.i[0]";
connectAttr "clippingOffset_4x4Mtx.o" "nearClipPlaneOffset_mulMtx.i[1]";
connectAttr "aimBlend_blendMtx.omat" "nearClipPlaneOffset_mulMtx.i[2]";
connectAttr "nearFilmOffset_mul.ox" "nearClipPlaneOffset_cmpMtx.itx";
connectAttr "nearFilmOffset_mul.oy" "nearClipPlaneOffset_cmpMtx.ity";
connectAttr "nearFitResolutionGate_mul.ox" "nearClipPlaneOffset_cmpMtx.isx";
connectAttr "nearFitResolutionGate_mul.oy" "nearClipPlaneOffset_cmpMtx.isy";
connectAttr "nearDistanceScale_mul.ox" "nearFilmOffset_mul.i1x";
connectAttr "nearDistanceScale_mul.oy" "nearFilmOffset_mul.i1y";
connectAttr "filmOffsetRate_mul.oy" "nearFilmOffset_mul.i2y";
connectAttr "filmOffsetRate_mul.ox" "nearFilmOffset_mul.i2x";
connectAttr "apertureRate_div.ox" "nearDistanceScale_mul.i1x";
connectAttr "apertureRate_div.oy" "nearDistanceScale_mul.i1y";
connectAttr "render_camShape.ncp" "nearDistanceScale_mul.i2x";
connectAttr "render_camShape.ncp" "nearDistanceScale_mul.i2y";
connectAttr "aperture_mul.ox" "apertureRate_div.i1x";
connectAttr "aperture_mul.oy" "apertureRate_div.i1y";
connectAttr "render_camShape.fl" "apertureRate_div.i2x";
connectAttr "render_camShape.fl" "apertureRate_div.i2y";
connectAttr "render_camShape.hfa" "aperture_mul.i1x";
connectAttr "render_camShape.vfa" "aperture_mul.i1y";
connectAttr "render_camShape.hfo" "filmOffsetRate_mul.i1x";
connectAttr "render_camShape.vfo" "filmOffsetRate_mul.i1y";
connectAttr "render_camShape.vfa" "filmOffsetRate_mul.i2y";
connectAttr "render_camShape.hfa" "filmOffsetRate_mul.i2x";
connectAttr "nearDistanceScale_mul.o" "nearFitResolutionGate_mul.i1";
connectAttr "horizontaResolutionGateRatio_div.ox" "nearFitResolutionGate_mul.i2y"
		;
connectAttr "filmAspectRatio_div.ox" "horizontaResolutionGateRatio_div.i1x";
connectAttr ":defaultResolution.dar" "horizontaResolutionGateRatio_div.i2x";
connectAttr "render_camShape.hfa" "filmAspectRatio_div.i1x";
connectAttr "render_camShape.vfa" "filmAspectRatio_div.i2x";
connectAttr "farClipPlaneOffset_cmpMtx.omat" "farClipPlaneOffset_mulMtx.i[0]";
connectAttr "clippingOffset_4x4Mtx.o" "farClipPlaneOffset_mulMtx.i[1]";
connectAttr "aimBlend_blendMtx.omat" "farClipPlaneOffset_mulMtx.i[2]";
connectAttr "farFilmOffset_mul.ox" "farClipPlaneOffset_cmpMtx.itx";
connectAttr "farFilmOffset_mul.oy" "farClipPlaneOffset_cmpMtx.ity";
connectAttr "farFitResolutionGate_mul.ox" "farClipPlaneOffset_cmpMtx.isx";
connectAttr "farFitResolutionGate_mul.oy" "farClipPlaneOffset_cmpMtx.isy";
connectAttr "farDistanceScale_mul.ox" "farFilmOffset_mul.i1x";
connectAttr "farDistanceScale_mul.oy" "farFilmOffset_mul.i1y";
connectAttr "filmOffsetRate_mul.oy" "farFilmOffset_mul.i2y";
connectAttr "filmOffsetRate_mul.ox" "farFilmOffset_mul.i2x";
connectAttr "apertureRate_div.ox" "farDistanceScale_mul.i1x";
connectAttr "apertureRate_div.oy" "farDistanceScale_mul.i1y";
connectAttr "render_camShape.fcp" "farDistanceScale_mul.i2x";
connectAttr "render_camShape.fcp" "farDistanceScale_mul.i2y";
connectAttr "farDistanceScale_mul.o" "farFitResolutionGate_mul.i1";
connectAttr "horizontaResolutionGateRatio_div.ox" "farFitResolutionGate_mul.i2y"
		;
connectAttr "rigSize_cmpMtx.omat" "settingSpacer_mulMtx.i[0]";
connectAttr "aimBlend_blendMtx.omat" "settingSpacer_mulMtx.i[1]";
connectAttr "aimUpTargetOffset_4x4Mtx.o" "aimUpTargetOffset_mulMtx.i[0]";
connectAttr "aimUpTargetRoll_cmpMtx.omat" "aimUpTargetOffset_mulMtx.i[1]";
connectAttr "allRigMatrix_mulMtx.o" "aimUpTargetOffset_mulMtx.i[2]";
connectAttr "unitConversion6.o" "aimUpTargetRoll_cmpMtx.irz";
connectAttr "aimTarget_C_ctrl.roll" "unitConversion6.i";
connectAttr ":time1.o" "cameraNoise_exp.tim";
connectAttr "shakeCamera_null.msg" "cameraNoise_exp.obm";
connectAttr "shakeCamera_null.proxyEnableShake" "cameraNoise_exp.in[0]";
connectAttr "shakeCamera_null.proxyEnableNoiseA" "cameraNoise_exp.in[1]";
connectAttr "shakeCamera_null.proxySeedA" "cameraNoise_exp.in[2]";
connectAttr "shakeCamera_null.proxySpeedA" "cameraNoise_exp.in[3]";
connectAttr "shakeCamera_null.proxyMagnitudeA" "cameraNoise_exp.in[4]";
connectAttr "shakeCamera_null.proxyEnableNoiseB" "cameraNoise_exp.in[5]";
connectAttr "shakeCamera_null.proxySeedB" "cameraNoise_exp.in[6]";
connectAttr "shakeCamera_null.proxySpeedB" "cameraNoise_exp.in[7]";
connectAttr "shakeCamera_null.proxyMagnitudeB" "cameraNoise_exp.in[8]";
connectAttr "shakeCamera_null.proxyEnableNoiseC" "cameraNoise_exp.in[9]";
connectAttr "shakeCamera_null.proxySeedC" "cameraNoise_exp.in[10]";
connectAttr "shakeCamera_null.proxySpeedC" "cameraNoise_exp.in[11]";
connectAttr "shakeCamera_null.proxyMagnitudeC" "cameraNoise_exp.in[12]";
connectAttr "shakeCamera_null.proxyEnableNoiseD" "cameraNoise_exp.in[13]";
connectAttr "shakeCamera_null.proxySeedD" "cameraNoise_exp.in[14]";
connectAttr "shakeCamera_null.proxySpeedD" "cameraNoise_exp.in[15]";
connectAttr "shakeCamera_null.proxyMagnitudeD" "cameraNoise_exp.in[16]";
connectAttr "shakeCamera_null.proxyEnableTX" "cameraNoise_exp.in[17]";
connectAttr "shakeCamera_null.proxyEnableTY" "cameraNoise_exp.in[18]";
connectAttr "shakeCamera_null.proxyEnableTZ" "cameraNoise_exp.in[19]";
connectAttr "shakeCamera_null.proxyEnableRX" "cameraNoise_exp.in[20]";
connectAttr "shakeCamera_null.proxyEnableRY" "cameraNoise_exp.in[21]";
connectAttr "shakeCamera_null.proxyEnableRZ" "cameraNoise_exp.in[22]";
connectAttr "cameraNoise_exp.out[3]" "unitConversion3.i";
connectAttr "cameraNoise_exp.out[4]" "unitConversion4.i";
connectAttr "cameraNoise_exp.out[5]" "unitConversion5.i";
connectAttr ":time1.o" "aimTargetNoise_exp.tim";
connectAttr "shakeAimTarget_null.msg" "aimTargetNoise_exp.obm";
connectAttr "shakeAimTarget_null.proxyEnableShake" "aimTargetNoise_exp.in[0]";
connectAttr "shakeAimTarget_null.proxyEnableNoiseA" "aimTargetNoise_exp.in[1]";
connectAttr "shakeAimTarget_null.proxySeedA" "aimTargetNoise_exp.in[2]";
connectAttr "shakeAimTarget_null.proxySpeedA" "aimTargetNoise_exp.in[3]";
connectAttr "shakeAimTarget_null.proxyMagnitudeA" "aimTargetNoise_exp.in[4]";
connectAttr "shakeAimTarget_null.proxyEnableNoiseB" "aimTargetNoise_exp.in[5]";
connectAttr "shakeAimTarget_null.proxySeedB" "aimTargetNoise_exp.in[6]";
connectAttr "shakeAimTarget_null.proxySpeedB" "aimTargetNoise_exp.in[7]";
connectAttr "shakeAimTarget_null.proxyMagnitudeB" "aimTargetNoise_exp.in[8]";
connectAttr "shakeAimTarget_null.proxyEnableTX" "aimTargetNoise_exp.in[9]";
connectAttr "shakeAimTarget_null.proxyEnableTY" "aimTargetNoise_exp.in[10]";
connectAttr "shakeAimTarget_null.proxyEnableTZ" "aimTargetNoise_exp.in[11]";
connectAttr "shakeFilm_null.proxyEnableShake" "expression1.in[0]";
connectAttr "shakeFilm_null.proxyEnableNoiseA" "expression1.in[1]";
connectAttr "shakeFilm_null.proxySeedA" "expression1.in[2]";
connectAttr "shakeFilm_null.proxySpeedA" "expression1.in[3]";
connectAttr "shakeFilm_null.proxyMagnitudeA" "expression1.in[4]";
connectAttr "shakeFilm_null.proxyEnableNoiseB" "expression1.in[5]";
connectAttr "shakeFilm_null.proxySeedB" "expression1.in[6]";
connectAttr "shakeFilm_null.proxySpeedB" "expression1.in[7]";
connectAttr "shakeFilm_null.proxyMagnitudeB" "expression1.in[8]";
connectAttr "shakeFilm_null.proxyEnableTX" "expression1.in[9]";
connectAttr "shakeFilm_null.proxyEnableTY" "expression1.in[10]";
connectAttr ":time1.o" "expression1.tim";
connectAttr "shakeFilm_null.msg" "expression1.obm";
connectAttr "nearClipPlane_C_ctrl.m" "gridGuideOffset_mulMtx.i[0]";
connectAttr "nearClipPlaneOffset_mulMtx.o" "gridGuideOffset_mulMtx.i[1]";
connectAttr "nearClipPlane_C_ctrlShape.ws" "frustumAA_pointInfo.ic";
connectAttr "farClipPlane_C_ctrlShape.ws" "frustumAB_pointInfo.ic";
connectAttr "nearClipPlane_C_ctrlShape.ws" "frustumBA_pointInfo.ic";
connectAttr "farClipPlane_C_ctrlShape.ws" "frustumBB_pointInfo.ic";
connectAttr "nearClipPlane_C_ctrlShape.ws" "frustumCA_pointInfo.ic";
connectAttr "farClipPlane_C_ctrlShape.ws" "frustumCB_pointInfo.ic";
connectAttr "nearClipPlane_C_ctrlShape.ws" "frustumDA_pointInfo.ic";
connectAttr "farClipPlane_C_ctrlShape.ws" "frustumDB_pointInfo.ic";
connectAttr "nearFarClipPlane_add.o" "nearClipPlaneBoost_mul.i1x";
connectAttr "nearFarClipPlane_add.o" "nearClipPlaneBoost_mul.i1y";
connectAttr "nearFarClipPlane_add.o" "nearClipPlaneBoost_mul.i1z";
connectAttr "render_camShape.ncp" "nearFarClipPlane_add.i1";
connectAttr "render_camShape.fcp" "nearFarClipPlane_add.i2";
connectAttr "settings_C_ctrl.verticalGuideOffset" "unitConversion1.i";
connectAttr "aperture_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "apertureRate_div.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "nearDistanceScale_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "filmOffsetRate_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "nearFilmOffset_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "farDistanceScale_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "farFilmOffset_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "nearClipPlaneBoost_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "nearFarClipPlane_add.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "allRigMatrix_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimTarget_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimUpTarget_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimParentA_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimParentB_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimParentC_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "allRig_condition.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimParentA_condition.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimParentB_condition.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimParentC_condition.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "filmAspectRatio_div.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "horizontaResolutionGateRatio_div.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "farFitResolutionGate_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "nearFitResolutionGate_mul.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimTargetOffset_4x4Mtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimTargetOffset_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimUpTargetOffset_4x4Mtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "aimUpTargetOffset_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "clippingOffset_4x4Mtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "nearClipPlaneOffset_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "farClipPlaneOffset_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "gridGuideOffset_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "filmOffsetSliderOffset_4x4Mtx.msg" ":defaultRenderUtilityList1.u" -na
		;
connectAttr "filmOffsetSliderAreaOffset_mulMtx.msg" ":defaultRenderUtilityList1.u"
		 -na;
connectAttr "filmOffsetSlider_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "filmOffset_add.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "settingSpacer_mulMtx.msg" ":defaultRenderUtilityList1.u" -na;
connectAttr "locatorScale_mul.msg" ":defaultRenderUtilityList1.u" -na;
// End of camera_rig_v01c.ma
