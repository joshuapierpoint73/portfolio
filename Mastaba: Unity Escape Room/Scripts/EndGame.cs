using UnityEngine;
using UnityEngine.SceneManagement;

public class EndGame : MonoBehaviour
{
    private GameTimer gameTimer;  // Reference to the GameTimer script

    void Start()
    {
        // Get the GameTimer script component in the scene
        gameTimer = FindObjectOfType<GameTimer>();
    }

    // Triggered when the player enters the trigger zone
    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            // Save the remaining time when player reaches exit
            if (gameTimer != null)
            {
                // Save the remaining time in PlayerPrefs
                PlayerPrefs.SetFloat("FinalTime", gameTimer.GetRemainingTime());
            }

            // Unlock the cursor and make it visible
            Cursor.lockState = CursorLockMode.None;  // Unlock the cursor
            Cursor.visible = true;  // Make the cursor visible

            // Load the "EndGame" scene
            SceneManager.LoadScene("EndGame");
        }
    }
}
