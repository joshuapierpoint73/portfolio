using UnityEngine;
using UnityEngine.SceneManagement;

public class MainMenu : MonoBehaviour
{
    // Loads the game scene
    public void PlayGame()
    {
        SceneManager.LoadScene("Game");
    }

    // Loads the controls screen
    public void OpenControls()
    {
        PlayerPrefs.SetString("PreviousScene", SceneManager.GetActiveScene().name);  // Optionally save the current scene
        SceneManager.LoadScene("Controls");  // Assuming the Controls screen is named "Controls"
    }

    // Loads the settings scene
    public void OpenSettings()
    {
        PlayerPrefs.SetString("PreviousScene", SceneManager.GetActiveScene().name);
        SceneManager.LoadScene("Settings");
    }

    // Quits the game and logs the action
        public void QuitGame()
    {
        Debug.Log("Game Quit");
        Application.Quit();
    }
}
