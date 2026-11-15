using UnityEngine;

/// <summary>
/// Zero-allocation spectrum lip-sync.
/// Maps low/mid/high bands to jaw, wide, and funnel shapes.
/// Replace the three shape names with your actual mouth blendshapes.
/// </summary>
[RequireComponent(typeof(AudioSource))]
public class LipSyncDriver : MonoBehaviour
{
    [SerializeField] private FaceDriver faceDriver;
    [SerializeField] private AudioSource audioSource;

    [Header("Shape Names (must match mesh)")]
    [SerializeField] private string jawOpen = "jawOpen";
    [SerializeField] private string mouthWide = "mouthSmile";
    [SerializeField] private string mouthFunnel = "mouthFunnel";

    [Header("Bands")]
    [SerializeField] private int spectrumSize = 256;
    [SerializeField] private FFTWindow window = FFTWindow.BlackmanHarris;

    private float[] spectrum;
    private float[] mouthWeights;
    private string[] mouthNames;

    private void Awake()
    {
        spectrum = new float[spectrumSize];
        mouthWeights = new float[3];
        mouthNames = new[] { jawOpen, mouthWide, mouthFunnel };

        if (faceDriver == null)
            faceDriver = GetComponent<FaceDriver>();
        if (audioSource == null)
            audioSource = GetComponent<AudioSource>();
    }

    private void Update()
    {
        if (audioSource == null || !audioSource.isPlaying)
        {
            for (int i = 0; i < mouthWeights.Length; i++)
                mouthWeights[i] = Mathf.MoveTowards(mouthWeights[i], 0f, Time.deltaTime * 10f);
        }
        else
        {
            audioSource.GetSpectrumData(spectrum, 0, window);
            AnalyzeBands();
        }

        faceDriver?.SetMouthWeights(mouthWeights, mouthNames);
    }

    private void AnalyzeBands()
    {
        // Rough formant bands for a 256-bin spectrum at 44.1/48 kHz
        float low = BandEnergy(2, 12);    // ~200-500 Hz  → jaw
        float mid = BandEnergy(12, 40);   // ~500-2000 Hz → wide
        float high = BandEnergy(40, 90);  // ~2-4 kHz     → funnel/fricative

        mouthWeights[0] = Mathf.Clamp01(low * 8f);
        mouthWeights[1] = Mathf.Clamp01(mid * 6f);
        mouthWeights[2] = Mathf.Clamp01(high * 5f);
    }

    private float BandEnergy(int startBin, int endBin)
    {
        float sum = 0f;
        int count = 0;
        for (int i = startBin; i < endBin && i < spectrum.Length; i++)
        {
            sum += spectrum[i];
            count++;
        }
        return count > 0 ? sum / count : 0f;
    }
}
