using UnityEngine;

public class MouseMovement : MonoBehaviour
{
    public float mouseSensitivity = 10000f;  // Sensitivity for mouse input
    public Transform playerBody;  // Reference to the player's body (for horizontal rotation)
    public Transform cameraTransform;  // Reference to the camera (for vertical rotation)

    private float xRotation = 0f;  // Store vertical rotation

    public static bool isLockUIOpen = false;  // Track if the lock UI is open
    private bool isSettingsMenuOpen = false;  // Track if the settings menu is open

    void Start()
    {
        // Lock cursor to the centre of the screen and hide it
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    void Update()
    {
        // Check if the settings menu is open (disable movement if true)
        isSettingsMenuOpen = SettingsInGame.Instance.isSettingsMenuOpen;

        // Only allow mouse movement if the inventory is not open, lock UI is not active, and settings menu is not open
        if (!InventorySystem.Instance.isOpen && !isLockUIOpen && !isSettingsMenuOpen)
        {
            // Get mouse input for horizontal and vertical movement
            float mouseX = Input.GetAxis("Mouse X") * mouseSensitivity * Time.deltaTime;
            float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity * Time.deltaTime;

            // Rotate player body horizontally (left/right)
            playerBody.Rotate(Vector3.up * mouseX);

            // Apply vertical camera rotation with clamping to prevent flipping
            xRotation -= mouseY;
            xRotation = Mathf.Clamp(xRotation, -90f, 90f);  // Limit vertical rotation range

            // Set the camera's local rotation
            cameraTransform.localRotation = Quaternion.Euler(xRotation, 0f, 0f);
        }
    }

    // Open the lock UI and unlock the cursor
    public static void OpenLockUI()
    {
        isLockUIOpen = true;
        Cursor.lockState = CursorLockMode.None;  // Unlock the cursor
        Cursor.visible = true;  // Show the cursor
    }

    // Close the lock UI and lock the cursor again
    public static void CloseLockUI()
    {
        isLockUIOpen = false;
        Cursor.lockState = CursorLockMode.Locked;  // Lock the cursor to the centre
        Cursor.visible = false;  // Hide the cursor
    }
}
