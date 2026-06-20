using UnityEngine;

public class PharaohRiddle : MonoBehaviour
{
    [Header("UI Elements")]
    public GameObject textBox;

    // Deactivates the text box UI
    public void ExitText()
    {
        textBox.SetActive(false);
    }
}
