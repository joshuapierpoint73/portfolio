using UnityEngine;
using UnityEngine.SceneManagement;

public class ControlsScreen : MonoBehaviour
{
    // This method will be called when the back button is pressed
    public void BackToMainMenu()
    {
        // Optionally, load the scene saved as "PreviousScene" in PlayerPrefs if you want to return there
        string previousScene = PlayerPrefs.GetString("PreviousScene", "MainMenu");  // Default to MainMenu if not set
        SceneManager.LoadScene(previousScene);
    }
}
