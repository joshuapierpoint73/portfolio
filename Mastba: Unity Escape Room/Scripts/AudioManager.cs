using UnityEngine;

public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    public AudioSource musicSource;
    public float sfxVolume = 1f;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    private void Start()
    {
        // Load saved settings
        float musicVol = PlayerPrefs.GetFloat("MusicVolume", 1f);
        float sfxVol = PlayerPrefs.GetFloat("SFXVolume", 1f);

        SetMusicVolume(musicVol);
        SetSFXVolume(sfxVol);
    }

    public void SetMusicVolume(float volume)
    {
        if (musicSource != null)
        {
            musicSource.volume = volume;
        }
        PlayerPrefs.SetFloat("MusicVolume", volume);
    }

    public void SetSFXVolume(float volume)
    {
        sfxVolume = volume;
        PlayerPrefs.SetFloat("SFXVolume", volume);
    }
}
