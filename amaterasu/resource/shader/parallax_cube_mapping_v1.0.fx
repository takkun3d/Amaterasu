// Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
#define BLEND_MODE_LIST "Normal:Darken:Multiply:Color Burn:Linear Burn:Lighten:Screen:Color Dodge:Add:Overlay:Soft Light:Hard Light:Difference:Exclusion:Subtract:Divide"
#define BLEND_MODE_MAX 15

static const float ONE_THIRD = 1.0 / 3.0;
static const float TWO_THIRDS = 2.0 / 3.0;

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
    AddressU = Clamp;
    AddressV = Clamp;
    AddressW = Clamp;
};

float UVMargin <
    string Object = "Main";
    string UIName = "UV Margin";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 0.02;
> = 0.005;

float MainDepth <
    string Object = "Main";
    string UIName = "Depth";
    string UIWidget = "Slider";
    float UIMin = 0.0001;
    float UIMax = 10.0;
> = 1.0;

bool Layer0_Enable <
    string Object = "Layer 0";
    string UIName = "Enable 0";
> = true;
float Layer0_Depth <
    string Object = "Layer 0";
    string UIName = "Depth 0";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
float Layer0_OffsetX <
    string Object = "Layer 0";
    string UIName = "Offset X 0";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
float Layer0_OffsetY <
    string Object = "Layer 0";
    string UIName = "Offset Y 0";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
int Layer0_BlendMode <
    string Object = "Layer 0";
    string UIName = "Blend Mode 0";
    string UIFieldNames = BLEND_MODE_LIST;
    int UIMin = 0;
    int UIMax = BLEND_MODE_MAX;
> = 0;
float Layer0_Opacity <
    string Object = "Layer 0";
    string UIName = "Opacity 0";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 1.0;

bool Layer1_Enable <
    string Object = "Layer 1";
    string UIName = "Enable 1";
> = true;
float Layer1_Depth <
    string Object = "Layer 1";
    string UIName = "Depth 1";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.25;
float Layer1_OffsetX <
    string Object = "Layer 1";
    string UIName = "Offset X 1";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
float Layer1_OffsetY <
    string Object = "Layer 1";
    string UIName = "Offset Y 1";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
int Layer1_BlendMode <
    string Object = "Layer 1";
    string UIName = "Blend Mode 1";
    string UIFieldNames = BLEND_MODE_LIST;
    int UIMin = 0;
    int UIMax = BLEND_MODE_MAX;
> = 0;
float Layer1_Opacity <
    string Object = "Layer 1";
    string UIName = "Opacity 1";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 1.0;

bool Layer2_Enable <
    string Object = "Layer 2";
    string UIName = "Enable 2";
> = true;
float Layer2_Depth <
    string Object = "Layer 2";
    string UIName = "Depth 2";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.5;
float Layer2_OffsetX <
    string Object = "Layer 2";
    string UIName = "Offset X 2";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
float Layer2_OffsetY <
    string Object = "Layer 2";
    string UIName = "Offset Y 2";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
int Layer2_BlendMode <
    string Object = "Layer 2";
    string UIName = "Blend Mode 2";
    string UIFieldNames = BLEND_MODE_LIST;
    int UIMin = 0;
    int UIMax = BLEND_MODE_MAX;
> = 0;
float Layer2_Opacity <
    string Object = "Layer 2";
    string UIName = "Opacity 2";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 1.0;

bool Layer3_Enable <
    string Object = "Layer 3";
    string UIName = "Enable 3";
> = true;
float Layer3_Depth <
    string Object = "Layer 3";
    string UIName = "Depth 3";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.75;
float Layer3_OffsetX <
    string Object = "Layer 3";
    string UIName = "Offset X 3";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
float Layer3_OffsetY <
    string Object = "Layer 3";
    string UIName = "Offset Y 3";
    string UIWidget = "Slider";
    float UIMin = -1.0;
    float UIMax = 1.0;
> = 0.0;
int Layer3_BlendMode <
    string Object = "Layer 3";
    string UIName = "Blend Mode 3";
    string UIFieldNames = BLEND_MODE_LIST;
    int UIMin = 0;
    int UIMax = BLEND_MODE_MAX;
> = 0;
float Layer3_Opacity <
    string Object = "Layer 3";
    string UIName = "Opacity 3";
    string UIWidget = "Slider";
    float UIMin = 0.0;
    float UIMax = 1.0;
> = 1.0;

struct VS_INPUT {
    float3 Pos : POSITION;
    float3 Normal : NORMAL;
    float3 Tangent : TANGENT;
    float2 UV : TEXCOORD0;
};

struct VS_OUTPUT {
    float4 Pos : SV_Position;
    float2 vUV : TEXCOORD0;
    float3 vWorldPos : TEXCOORD1;
    float3 vNormal : NORMAL;
    float3 vTangent : TANGENT;
};

VS_OUTPUT VS(VS_INPUT input) {
    VS_OUTPUT output;

    // Transform the vertex position from object space to clip space
    output.Pos = mul(float4(input.Pos, 1.0), WorldViewProj);

    // Pass through the texture coordinates (UVs) to the pixel shader
    output.vUV = input.UV;

    // Calculate the 3D world space position of the vertex
    output.vWorldPos = mul(float4(input.Pos, 1.0), World).xyz;

    // Transform the normal vector to world space
    output.vNormal = normalize(mul(float4(input.Normal, 0.0), WorldInverseTranspose).xyz);

    // Transform the tangent vector to world space
    output.vTangent = normalize(mul(float4(input.Tangent, 0.0), World).xyz);

    return output;
}

float3 calcTangentViewDir(float3 worldPos, float3 camPos, float3 normal, float3 tangent) {
    // Calculate the normalized view ray direction from camera to the pixel
    float3 V = normalize(worldPos - camPos);

    // Compute the bitangent vector to complete the TBN basis
    float3 B = cross(normal, tangent);

    // Flip the normal if looking at the backface to ensure
    float3 N = (dot(V, normal) > 0.0) ? -normal : normal;

    // Transform the view ray direction into tangent space
    return float3(dot(V, tangent), dot(V, B), dot(V, N));
}

float3 applyBlendMode(int mode, float3 a, float3 b, float alpha) {
    float3 c = a;
    if (mode == 0) { // Normal
        c = b;

    } else if (mode == 1) { // Darken
        c = min(a, b);

    } else if (mode == 2) { // Multiply
        c = a * b;

    } else if (mode == 3) { // Color Burn
        c = max(1.0 - (1.0 - a) / (b + 0.000001), 0.0);

    } else if (mode == 4) { // Linear Burn
        c = max(a + b - 1.0, 0.0);

    } else if (mode == 5) { // Lighten
        c = max(a, b);

    } else if (mode == 6) { // Screen
        c = 1.0 - (1.0 - a) * (1.0 - b);

    } else if (mode == 7) { // Color Dodge
        c = min(a / (1.0 - b + 0.000001), 1.0);

    } else if (mode == 8) { // Add
        c = min(a + b, 1.0);

    } else if (mode == 9) { // Overlay
        c = lerp(2.0 * a * b, 1.0 - 2.0 * (1.0 - a) * (1.0 - b), step(0.5, a));

    } else if (mode == 10) { // Soft Light
        c = lerp(2.0 * a * b + a * a * (1.0 - 2.0 * b), sqrt(a) * (2.0 * b - 1.0) + 2.0 * a * (1.0 - b), step(0.5, b));

    } else if (mode == 11) { // Hard Light
        c = lerp(2.0 * a * b, 1.0 - 2.0 * (1.0 - b) * (1.0 - a), step(0.5, b));

    } else if (mode == 12) { // Difference
        c = abs(a - b);

    } else if (mode == 13) { // Exclusion
        c = a + b - 2.0 * a * b;

    } else if (mode == 14) { // Subtract
        c = max(a - b, 0.0);

    } else if (mode == 15) { // Divide
        c = min(a / (b + 0.000001), 1.0);
    }
    return lerp(a, c, alpha);
}

float2 calcCubeUV(float2 startUV, float3 rayDir, float depth) {
    // Initialize the ray origin on the 2D surface (Z = 0.0)
    float3 rayPos = float3(startUV, 0.0);

    // Precompute the inverse ray direction to optimize intersection calculations
    float3 invRay = 1.0 / rayDir;

    // Determine the target wall coordinates (0.0 or 1.0) based on ray direction
    float3 wallTarget = step(0.0, rayDir);

    // Calculate the distance to each plane using the slab method (tx, ty, tz)
    float tx = (wallTarget.x - rayPos.x) * invRay.x;
    float ty = (wallTarget.y - rayPos.y) * invRay.y;
    float tz = (depth - rayPos.z) * invRay.z;

    // Select the closest intersection distance
    float tHit = min(tx, min(ty, tz));

    // Calculate the exact 3D intersection point
    float3 hitPos = rayPos + rayDir * tHit;

    // Normalize the Z depth for texture mapping (0.0 to 1.0 range)
    float normZ = hitPos.z / depth;

    // Calc uv
    if (step(tx, tHit) == 1.0) {
        if (wallTarget.x >= 0.5) { // Right
            return float2(3.0 - normZ, 2.0 - hitPos.y) * ONE_THIRD;

        } else {
            return float2(normZ, 2.0 - hitPos.y) * ONE_THIRD;
        }
    }

    if (step(ty, tHit) == 1.0) {
        if (wallTarget.y >= 0.5) { // Top
            return float2(hitPos.x + 1.0, normZ) * ONE_THIRD;

        } else {
            return float2(hitPos.x + 1.0, 3.0 - normZ) * ONE_THIRD;
        }
    }

    // Back
    return float2(hitPos.x + 1.0, 2.0 - hitPos.y) * ONE_THIRD;
}

float3 calcPlaneUV(float2 startUV, float3 rayDir, float depth, float2 offset) {
    // Calculate the intersection point of the view ray with the layer plane
    float2 hitPos = startUV - (rayDir.xy / rayDir.z) * depth;

    // Apply the custom 2D texture offset
    float2 offsetBaseUv = hitPos + offset;

    // Create a clipping mask to prevent texture repeating
    // 1.0 if inside [0, 1] bounds
    // 0.0 if outside
    float maskX = step(0.0, offsetBaseUv.x) * step(offsetBaseUv.x, 1.0);
    float maskY = step(0.0, offsetBaseUv.y) * step(offsetBaseUv.y, 1.0);
    float mask = maskX * maskY;

    // Apply UV margin to prevent texture bleeding from adjacent atlas tiles.
    offsetBaseUv = lerp(float2(UVMargin, UVMargin), float2(1.0 - UVMargin, 1.0 - UVMargin), offsetBaseUv);

    // Invert the Y-axis for correct texture orientation and scale down for
    // the 3x3 texture atlas
    float2 uv = float2(offsetBaseUv.x, 1.0 - offsetBaseUv.y) * ONE_THIRD;
    return float3(uv.x, uv.y, mask);
}

float4 PS(VS_OUTPUT input) : SV_Target {
    float3 rayDir = calcTangentViewDir(
        input.vWorldPos,
        ViewInverse[3].xyz,
        input.vNormal,
        input.vTangent
    );

    float2 mainUv = calcCubeUV(input.vUV, rayDir, -MainDepth);
    float3 finalRgb = MainTexture.Sample(MainSampler, mainUv).rgb;

    bool enables[4] = {
        Layer0_Enable,
        Layer1_Enable,
        Layer2_Enable,
        Layer3_Enable
    };
    float depths[4] = {
        MainDepth * Layer0_Depth,
        MainDepth * Layer1_Depth,
        MainDepth * Layer2_Depth,
        MainDepth * Layer3_Depth
    };
    float opacities[4] = {
        Layer0_Opacity,
        Layer1_Opacity,
        Layer2_Opacity,
        Layer3_Opacity
    };
    int modes[4] = {
        Layer0_BlendMode,
        Layer1_BlendMode,
        Layer2_BlendMode,
        Layer3_BlendMode
    };
    float2 offsets[4] = {
        float2(Layer0_OffsetX, Layer0_OffsetY),
        float2(Layer1_OffsetX, Layer1_OffsetY),
        float2(Layer2_OffsetX, Layer2_OffsetY),
        float2(Layer3_OffsetX, Layer3_OffsetY)
    };
    float2 uvTiles[4] = {
        float2(0.0, 0.0),
        float2(TWO_THIRDS, 0.0),
        float2(0.0, TWO_THIRDS),
        float2(TWO_THIRDS, TWO_THIRDS)
    };

    // Sorting Network
    int indices[4] = { 0, 1, 2, 3 };
    int tmp;
    #define SORT(i, j) if(depths[indices[i]] < depths[indices[j]]) { tmp = indices[i]; indices[i] = indices[j]; indices[j] = tmp; }
    SORT(0, 1); // tier 1
    SORT(2, 3);
    SORT(0, 2); // tier 2
    SORT(1, 3);
    SORT(1, 2); // tier 3
    #undef SORT

    for (int j = 0; j < 4; ++j) {
        int i = indices[j];
        if (!enables[i]) {
            continue;
        }

        float3 layerUv = calcPlaneUV(input.vUV, rayDir, depths[i], -offsets[i]);
        if (layerUv.z == 0.0) {
            continue;
        }

        float2 finalLayerUv = layerUv.xy + uvTiles[i];
        float4 layerTex = MainTexture.Sample(MainSampler, finalLayerUv);
        float alpha = layerTex.a * opacities[i];
        finalRgb = applyBlendMode(modes[i], finalRgb, layerTex.rgb, alpha);
    }

    return float4(finalRgb, 1.0);
}

technique11 Main {
    pass P0 {
        SetVertexShader(CompileShader(vs_5_0, VS()));
        SetPixelShader(CompileShader(ps_5_0, PS()));
    }
}