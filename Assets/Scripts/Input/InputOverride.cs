using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Joystick + face-button / D-pad override layer.
/// Highest priority. Blends on top of agent baseline motion.
/// </summary>
public class InputOverride : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Transform headBone;
    [SerializeField] private Transform leftArmIK;
    [SerializeField] private Transform rightArmIK;
    [SerializeField] private SkinnedMeshRenderer faceMesh;

    [Header("Sensitivity")]
    [SerializeField] private float headSensitivity = 45f;
    [SerializeField] private float armSensitivity = 1f;

    private Vector2 lookInput;
    private Vector2 moveInput;

    public void OnLook(InputAction.CallbackContext ctx) => lookInput = ctx.ReadValue<Vector2>();
    public void OnMove(InputAction.CallbackContext ctx) => moveInput = ctx.ReadValue<Vector2>();

    public void OnFaceButton(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        // Map X/Square/Triangle/Circle or D-pad to pre-baked actions
        // Example: trigger a blendshape or animation trigger
        Debug.Log($"Action triggered: {ctx.action.name}");
    }

    private void LateUpdate()
    {
        if (headBone != null)
        {
            float yaw = lookInput.x * headSensitivity * Time.deltaTime;
            float pitch = -lookInput.y * headSensitivity * Time.deltaTime;
            headBone.Rotate(pitch, yaw, 0f, Space.Self);
        }

        // Arm IK targets follow moveInput or separate sticks
        // Agent baseline is applied earlier; this overrides
    }
}
