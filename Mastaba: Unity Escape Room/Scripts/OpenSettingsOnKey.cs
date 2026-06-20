using UnityEngine;
using UnityEngine.SceneManagement;

public class OpenSettingsOnKey : MonoBehaviour
{
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Q))
        {
            // Save the current scene name to return to later
            string currentScene = SceneManager.GetActiveScene().name;
            PlayerPrefs.SetString("PreviousScene", currentScene);

            // Load the settings scene
            SceneManager.LoadScene("Settings");
        }
    }
}
