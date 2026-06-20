using UnityEngine;
using TMPro;  // Use TMPro namespace for TextMeshProUGUI
using UnityEngine.SceneManagement;

public class GameTimer : MonoBehaviour
{
    public static GameTimer Instance { get; private set; }  // Singleton instance
    public TextMeshProUGUI timerText;  // UI TextMeshProUGUI element to display the timer
    private float timeRemaining = 3600f;  // 60 minutes in seconds (3600s)

    void Awake()
    {
        // Ensure that only one instance of GameTimer exists
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);  // Destroy duplicates
        }
    }

    void Update()
    {
        // Decrease the timer by 1 second each frame
        if (timeRemaining > 0)
        {
            timeRemaining -= Time.deltaTime;
            UpdateTimerDisplay();
        }
        else
        {
            timeRemaining = 0;
            // Trigger end game when timer reaches 0
            TriggerEndGame();
        }
    }

    private void UpdateTimerDisplay()
    {
        int minutes = Mathf.FloorToInt(timeRemaining / 60);
        int seconds = Mathf.FloorToInt(timeRemaining % 60);
        timerText.text = string.Format("{0:00}:{1:00}", minutes, seconds);
    }

    private void TriggerEndGame()
    {
        // Store the remaining time in PlayerPrefs
        PlayerPrefs.SetFloat("FinalTime", timeRemaining);

        // Load the "EndGame" scene
        SceneManager.LoadScene("EndGame");
    }

    // New method to get the remaining time for external access
    public float GetRemainingTime()
    {
        return timeRemaining;
    }

    public void RemoveTimeForHint()
    {
        // Decrease the timer by 5 minutes (300 seconds)
        timeRemaining = Mathf.Max(0, timeRemaining - 300f);
        UpdateTimerDisplay();  // Update the display immediately
    }

}
