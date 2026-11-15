using UnityEngine;

/// <summary>
/// Locks the app to 60 FPS and applies the Pixel 10 Pro runtime constraints.
/// Attach to a bootstrap object in the first scene.
/// </summary>
public class PerformanceLock : MonoBehaviour
{
    [SerializeField] private int targetFrameRate = 60;

    private void Awake()
    {
        Application.targetFrameRate = targetFrameRate;
        QualitySettings.vSyncCount = 0;
        // Vulkan is set in Player Settings. ASTC is set on the baked textures.
    }
}
