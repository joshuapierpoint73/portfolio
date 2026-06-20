using System.Collections;
using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class FlashlightController : MonoBehaviour
{
    private Light flashlight;
    private bool isOn = false;
    private bool isToggling = false;

    public AudioClip toggleSound;
    private AudioSource audioSource;

    void Start()
    {
        flashlight = GetComponentInChildren<Light>();
        if (flashlight == null)
        {
            Debug.LogError("No Light component found in child objects!");
        }

        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }

        if (AudioManager.Instance != null)
        {
            audioSource.volume = AudioManager.Instance.sfxVolume;
        }
    }

    void Update()
    {
        if (flashlight != null && Input.GetKeyDown(KeyCode.F) && !isToggling)
        {
            StartCoroutine(ToggleFlashlightWithDelay());
        }
    }

    private IEnumerator ToggleFlashlightWithDelay()
    {
        isToggling = true;

        if (toggleSound != null && AudioManager.Instance != null)
        {
            audioSource.volume = AudioManager.Instance.sfxVolume;
            audioSource.PlayOneShot(toggleSound);
        }

        yield return new WaitForSeconds(0.5f);

        isOn = !isOn;
        flashlight.enabled = isOn;
        isToggling = false;
    }
}
