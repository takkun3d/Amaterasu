// This file contains derivative work based on "jiWindowBox":
// Copyright 2018 Autodesk Inc, All rights reserved.
// Licensed under the Apache License, Version 2.0.
// https://github.com/ADN-DevTech/3dsMax-OSL-Shaders/blob/master/LICENSE.txt
//
// Modifications from the original by takkun (takkun3d):
// - Ported from OSL to HLSL for real-time DirectX viewport rendering.
// - Added layer.
// - Applied mathematical and performance optimizations.

#define ONE_THIRD (1.0 / 3.0)
#define TWO_THIRDS (2.0 / 3.0)

float4x4 WorldViewProj : WorldViewProjection;
float4x4 World : World;
float4x4 WorldInverseTranspose : WorldInverseTranspose;
float4x4 ViewInverse : ViewInverse;

Texture2D MainTexture <
    string Object = "Main";
    string UIName = "Texture";
>;

SamplerState MainSampler {
    Filter = MIN_MAG_MIP_LINEAR;
    AddressU = WRAP;
    AddressV = WRAP;
};

float MainDepth <
    string Object = "Main";
    string UIName = "Depth";
    string UIWidget = "Slider";
    float UIMin = 0.001;
    float UIMax = 10.0;
> = 1.0;

bool EnableLayer0 <
    string Object = "Layer 0";
    string UIName = "Enable";
> = true;
float DepthLayer0 <
    string Object = "Layer 0";
    string UIName = "Depth";
    string UIWidget = "Slider";
    float UIMin = 0.0; float UIMax = 1.0;
> = 0.0;

bool EnableLayer1 <
    string Object = "Layer 1";
    string UIName = "Enable";
> = true;
float DepthLayer1 <
    string Object = "Layer 1";
    string UIName = "Depth";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 0.25;

bool EnableLayer2 <
    string Object = "Layer 2";
    string UIName = "Enable";
> = true;
float DepthLayer2 <
    string Object = "Layer 2";
    string UIName = "Depth";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 0.5;

bool EnableLayer3 <
    string Object = "Layer 3";
    string UIName = "Enable";
> = true;
float DepthLayer3 <
    string Object = "Layer 3";
    string UIName = "Depth";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 0.75;

struct VS_INPUT {
    float3 Pos : POSITION;
    float3 Normal : NORMAL;
    float3 Tangent : TANGENT;
    float2 UV : TEXCOORD0;
};

struct VS_OUTPUT {
    float4 Pos : SV_POSITION;
    float2 vUV : TEXCOORD0;
    float3 vWorldPos : TEXCOORD1;
    float3 vNormal : NORMAL;
    float3 vTangent : TANGENT;
};

VS_OUTPUT VS(VS_INPUT IN) {
    VS_OUTPUT OUT;

    OUT.Pos = mul(float4(IN.Pos, 1.0), WorldViewProj);
    OUT.vUV = IN.UV;
    OUT.vWorldPos = mul(float4(IN.Pos, 1.0), World).xyz;
    OUT.vNormal = normalize(mul(float4(IN.Normal, 0.0), WorldInverseTranspose).xyz);
    OUT.vTangent = normalize(mul(float4(IN.Tangent, 0.0), World).xyz);

    return OUT;
}

float4 PS(VS_OUTPUT IN) : SV_Target {
    bool4 enableLayers = bool4(EnableLayer0, EnableLayer1, EnableLayer2, EnableLayer3);
    float depths[4] = {
        clamp(MainDepth * DepthLayer0, 0.0001, MainDepth - 0.0001),
        clamp(MainDepth * DepthLayer1, 0.0001, MainDepth - 0.0001),
        clamp(MainDepth * DepthLayer2, 0.0001, MainDepth - 0.0001),
        clamp(MainDepth * DepthLayer3, 0.0001, MainDepth - 0.0001)
    };
    const float3 layerOffsetUvs[4] = {float3(0.0, 0.0, 0.0), float3(TWO_THIRDS, 0.0, 0.0), float3(0.0, TWO_THIRDS, 0.0), float3(TWO_THIRDS, TWO_THIRDS, 0.0)};

    int indices[4] = {0, 1, 2, 3};
    int tmp;
    #define SWAP(a, b) if(depths[indices[a]] < depths[indices[b]]) { tmp = indices[a]; indices[a] = indices[b]; indices[b] = tmp; }
    SWAP(0, 1);
    SWAP(2, 3);
    SWAP(0, 2);
    SWAP(1, 3);
    SWAP(1, 2);
    #undef SWAP

    float3 cameraPos = mul(float4(0.0, 0.0, 0.0, 1.0), ViewInverse).xyz;
    float3 V = normalize(IN.vWorldPos - cameraPos);
    float3 N = IN.vNormal;
    float3 T = IN.vTangent;
    float3 B = cross(N, T);
    if (dot(V, N) > 0.0) {
        N = -N;
    }

    float3 R = float3(dot(V, T), dot(V, B), dot(V, N));
    float3 invR = 1.0 / (-R);
    float3 P = float3(IN.vUV.x, IN.vUV.y, 0.5);
    float3 S = step(0.0, R);

    float3 baseDepth = (P - S) * (invR / MainDepth);
    float3 baseBack  = (P - S) * invR;
    float3 baseWidth = baseDepth * MainDepth;

    float2 fcRaw = float2(baseWidth.y, baseDepth.y) * R.xz + P.xz + float2(0.0, 0.5);
    float2 swRaw = float2(baseDepth.x, baseWidth.x) * R.zy + P.zy + float2(0.5, 0.0);

    float fcMask = step(0.0, fcRaw.y) * step(0.0, 1.0 - max(fcRaw.x, 1.0 - fcRaw.x));
    float3 fcUv = float3(fcRaw, 0.0) / 3.0;

    float3 ceilUv = float3(fcUv.x + ONE_THIRD, ONE_THIRD - fcUv.y, 0.0) * fcMask * S.y;
    float3 floorUv = float3(fcUv.x + ONE_THIRD, TWO_THIRDS + fcUv.y, 0.0) * fcMask * (1.0 - S.y);

    float swMask = step(0.0, swRaw.x) * step(0.0, 1.0 - max(swRaw.y, 1.0 - swRaw.y));
    float3 swUv = float3(swRaw, 0.0) / 3.0;

    float3 lWallUv = float3(ONE_THIRD - swUv.x, TWO_THIRDS - swUv.y, 0.0) * swMask * (1.0 - S.x);
    float3 rWallUv = float3(swUv.x + TWO_THIRDS, TWO_THIRDS - swUv.y, 0.0) * swMask * S.x;

    float2 backRaw = (baseBack.z * R.xy + (P.xy / 2.0) / MainDepth) * (MainDepth * 2.0) / 3.0;
    float3 bWallUv = float3(backRaw.x + ONE_THIRD, TWO_THIRDS - backRaw.y, 0.0) * (1.0 - max(step(0.0, swRaw.x), step(0.0, fcRaw.y)));

    float3 finalUv = ceilUv + floorUv + bWallUv + lWallUv + rWallUv;
    float3 finalRgb = MainTexture.Sample(MainSampler, finalUv.xy).rgb;

    for (int j = 0; j < 4; ++j) {
        int i = indices[j];
        if (enableLayers[i]) {
            float d2 = depths[i] * 2.0;
            float3 rawUv = ((baseBack.z * R + P / d2) * d2 / 3.0);
            float3 layerUv = float3(rawUv.x, ONE_THIRD - rawUv.y, 0.0);
            float layerMask = step(0.0, layerUv.y * 3.0 * (1.0 - layerUv.y * 3.0)) * step(0.0, layerUv.x * (ONE_THIRD - layerUv.x));
            layerUv += layerOffsetUvs[i];

            float4 layerTex = MainTexture.Sample(MainSampler, layerUv.xy);
            finalRgb = lerp(finalRgb, layerTex.rgb, layerTex.a * layerMask);
        }
    }

    return float4(finalRgb, 1.0);
}

technique11 Main {
    pass P0 {
        SetVertexShader(CompileShader(vs_5_0, VS()));
        SetPixelShader(CompileShader(ps_5_0, PS()));
    }
}