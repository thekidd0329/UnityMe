using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Plays agent timeline locked to AudioSource.time when available.
/// Drives lights, expressions (via FaceDriver), and simple camera/groove cues.
/// </summary>
public class AgentDirector : MonoBehaviour
{
    [Serializable]
    public class TimelineEvent
    {
        public float time;
        public string type;
        public string target;
        public float value;
        public bool hold;
    }

    [Serializable]
    public class Timeline
    {
        public List<TimelineEvent> events = new List<TimelineEvent>();
    }

    [Header("References")]
    [SerializeField] private FaceDriver faceDriver;
    [SerializeField] private Light keyLight;
    [SerializeField] private Light rimLight;
    [SerializeField] private AudioSource audioSource;

    [Header("Timeline")]
    [SerializeField] private TextAsset timelineJson;

    private Timeline timeline;
    private int nextEventIndex;
    private bool isPlaying;

    private void Start()
    {
        if (timelineJson != null)
            LoadTimeline(timelineJson.text);
    }

    public void LoadTimeline(string json)
    {
        timeline = JsonUtility.FromJson<Timeline>(json);
        if (timeline?.events != null)
            timeline.events.Sort((a, b) => a.time.CompareTo(b.time));
        nextEventIndex = 0;
    }

    public void Play()
    {
        isPlaying = true;
        nextEventIndex = 0;
    }

    public void Stop() => isPlaying = false;

    private void Update()
    {
        if (!isPlaying || timeline?.events == null) return;

        float t = (audioSource != null && audioSource.isPlaying)
            ? audioSource.time
            : Time.time; // fallback only

        while (nextEventIndex < timeline.events.Count &&
               timeline.events[nextEventIndex].time <= t)
        {
            ApplyEvent(timeline.events[nextEventIndex]);
            nextEventIndex++;
        }
    }

    private void ApplyEvent(TimelineEvent e)
    {
        switch (e.type)
        {
            case "light":
                var light = e.target == "rim" ? rimLight : keyLight;
                if (light != null) light.intensity = e.value;
                break;

            case "expression":
                faceDriver?.SetExpression(e.target, e.value, e.hold);
                break;

            case "camera":
                // Wire to Cinemachine priority or your camera rig here
                break;

            case "groove":
                // Trigger baseline body clip if you have an Animator
                break;
        }
    }
}
