using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Drives facial blendshapes.
/// Mouth shapes come from LipSyncDriver every frame.
/// Other expressions are set by name (agent or buttons) and decay unless held.
/// </summary>
[RequireComponent(typeof(SkinnedMeshRenderer))]
public class FaceDriver : MonoBehaviour
{
    [Header("Mesh")]
    [SerializeField] private SkinnedMeshRenderer faceRenderer;

    [Header("Lip Sync")]
    [Tooltip("Blendshape names that lip-sync is allowed to drive.")]
    [SerializeField] private string[] mouthBlendshapeNames;

    [Header("Expression")]
    [SerializeField] private float expressionDecay = 6f;

    private Dictionary<string, int> nameToIndex;
    private bool[] isMouthShape;
    private bool[] expressionHold;
    private float[] expressionTargets;
    private float[] expressionCurrent;
    private int blendShapeCount;

    private void Awake()
    {
        if (faceRenderer == null)
            faceRenderer = GetComponent<SkinnedMeshRenderer>();

        var mesh = faceRenderer.sharedMesh;
        blendShapeCount = mesh.blendShapeCount;

        nameToIndex = new Dictionary<string, int>(blendShapeCount);
        isMouthShape = new bool[blendShapeCount];
        expressionHold = new bool[blendShapeCount];
        expressionTargets = new float[blendShapeCount];
        expressionCurrent = new float[blendShapeCount];

        for (int i = 0; i < blendShapeCount; i++)
        {
            string n = mesh.GetBlendShapeName(i);
            nameToIndex[n] = i;
        }

        if (mouthBlendshapeNames != null)
        {
            foreach (var n in mouthBlendshapeNames)
            {
                if (nameToIndex.TryGetValue(n, out int idx))
                    isMouthShape[idx] = true;
            }
        }
    }

    public bool TryGetIndex(string blendshapeName, out int index)
    {
        return nameToIndex.TryGetValue(blendshapeName, out index);
    }

    /// <summary>
    /// Lip-sync path. weights are 0-1.
    /// </summary>
    public void SetMouthWeights(float[] weights, string[] shapeNames)
    {
        if (weights == null || shapeNames == null) return;
        int n = Mathf.Min(weights.Length, shapeNames.Length);
        for (int i = 0; i < n; i++)
        {
            if (!nameToIndex.TryGetValue(shapeNames[i], out int idx)) continue;
            if (!isMouthShape[idx]) continue;
            faceRenderer.SetBlendShapeWeight(idx, Mathf.Clamp01(weights[i]) * 100f);
        }
    }

    public void SetExpression(string blendshapeName, float weight, bool hold = false)
    {
        if (!nameToIndex.TryGetValue(blendshapeName, out int idx)) return;
        if (isMouthShape[idx]) return; // mouth is owned by lip-sync

        expressionTargets[idx] = Mathf.Clamp01(weight);
        expressionHold[idx] = hold;
    }

    public void ClearExpression(string blendshapeName)
    {
        if (!nameToIndex.TryGetValue(blendshapeName, out int idx)) return;
        expressionHold[idx] = false;
        expressionTargets[idx] = 0f;
    }

    private void LateUpdate()
    {
        for (int i = 0; i < blendShapeCount; i++)
        {
            if (isMouthShape[i]) continue;

            if (!expressionHold[i])
                expressionTargets[i] = 0f;

            expressionCurrent[i] = Mathf.MoveTowards(
                expressionCurrent[i],
                expressionTargets[i],
                expressionDecay * Time.deltaTime);

            faceRenderer.SetBlendShapeWeight(i, expressionCurrent[i] * 100f);
        }
    }
}
