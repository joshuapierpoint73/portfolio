using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class HarpPuzzle : MonoBehaviour
{
    public static HarpPuzzle Instance { get; private set; }

    private readonly string[] correctSequence = { "Small", "Large", "Small", "Medium" };
    private readonly List<string> playerSequence = new List<string>();

    private float sequenceTimer = 0f;
    private const float maxTime = 20f;

    public GameObject Door;

    public AudioClip harpSmallClip;
    public AudioClip harpLargeClip;
    public AudioClip harpMediumClip;
    private AudioSource audioSource;

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
        }
    }

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>(); // fixed: now assigns properly
        }

        if (harpSmallClip == null || harpLargeClip == null || harpMediumClip == null)
        {
            Debug.LogError("One or more harp sound clips are not assigned!");
        }
    }

    void Update()
    {
        sequenceTimer += Time.deltaTime;
        if (sequenceTimer >= maxTime)
        {
            ResetSequence();
        }
    }

    public void PlayHarp(string harpSize)
    {
        playerSequence.Add(harpSize);

        if (playerSequence.Count > correctSequence.Length)
        {
            playerSequence.RemoveAt(0);
        }

        PlayHarpSound(harpSize);
        CheckSequence();
    }

    private void PlayHarpSound(string harpSize)
    {
        if (audioSource == null)
        {
            Debug.LogError("No AudioSource attached to this object.");
            return;
        }

        float sfxVolume = AudioManager.Instance != null ? AudioManager.Instance.sfxVolume : 1f;

        switch (harpSize)
        {
            case "Small":
                if (harpSmallClip != null)
                {
                    audioSource.PlayOneShot(harpSmallClip, sfxVolume);
                }
                else
                {
                    Debug.LogError("HarpSmallClip is missing!");
                }
                break;
            case "Large":
                if (harpLargeClip != null)
                {
                    audioSource.PlayOneShot(harpLargeClip, sfxVolume);
                }
                else
                {
                    Debug.LogError("HarpLargeClip is missing!");
                }
                break;
            case "Medium":
                if (harpMediumClip != null)
                {
                    audioSource.PlayOneShot(harpMediumClip, sfxVolume);
                }
                else
                {
                    Debug.LogError("HarpMediumClip is missing!");
                }
                break;
            default:
                Debug.LogWarning($"Unknown harp size: {harpSize}");
                break;
        }
    }

    private void CheckSequence()
    {
        if (playerSequence.Count == correctSequence.Length)
        {
            for (int i = 0; i < correctSequence.Length; i++)
            {
                if (playerSequence[i] != correctSequence[i])
                {
                    ResetSequence();
                    return;
                }
            }
            SolvePuzzle();
        }
    }

    private void SolvePuzzle()
    {
        Debug.Log("Correct harp sequence! Opening door.");
        Door.GetComponent<DoorScript>().Open();
    }

    private void ResetSequence()
    {
        playerSequence.Clear();
        sequenceTimer = 0f;
        Debug.Log("Sequence reset due to timeout.");
    }
}
