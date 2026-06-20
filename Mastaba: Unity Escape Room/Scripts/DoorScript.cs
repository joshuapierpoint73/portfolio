using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class DoorScript : MonoBehaviour
{
    private Vector3 startPosition;
    private Vector3 endPosition;

    public AudioClip doorOpenSound;
    private AudioSource audioSource;

    private void Start()
    {
        startPosition = transform.position;
        endPosition = new Vector3(startPosition.x, startPosition.y + 100f, startPosition.z);

        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }

        // Set initial volume from AudioManager
        if (AudioManager.Instance != null)
        {
            audioSource.volume = AudioManager.Instance.sfxVolume;
        }
    }

    public void Open()
    {
        transform.position = Vector3.Lerp(startPosition, endPosition, 1f);

        // Play the door opening sound
        if (doorOpenSound != null && AudioManager.Instance != null)
        {
            audioSource.volume = AudioManager.Instance.sfxVolume; // Update volume in case settings changed
            audioSource.PlayOneShot(doorOpenSound);
        }
    }
}
