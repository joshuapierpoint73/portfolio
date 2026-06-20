using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

[RequireComponent(typeof(BoxCollider))]
public class ChestLockSystem : MonoBehaviour
{
    private Animator animator;
    private BoxCollider chestCollider;

    public GameObject lockScreenUI;
    public GameObject lockScreenUI2;
    public TextMeshProUGUI[] digitTexts;
    public TextMeshProUGUI[] letterTexts;

    private int[] digits = new int[4];
    private char[] letters = new char[5];

    public string correctCode;
    public string correctWord;
    public bool isOpen = false;
    public string lockType;

    // Available letters should only be required for Letter Lock chests
    public char[] availableLetters;

    public Button[] increaseNumButtons;
    public Button[] decreaseNumButtons;
    public Button[] increaseLetterButtons;
    public Button[] decreaseLetterButtons;

    public Button checkCodeButton;
    public Button closeLockUIButton;
    public Button checkCodeButton2;
    public Button closeLockUIButton2;

    // Audio
    public AudioClip chestOpenSound;
    private AudioSource audioSource;

    // New: Name of the chest (set in Inspector)
    public string ChestName;

    private void Start()
    {
        animator = GetComponentInParent<Animator>();
        chestCollider = GetComponent<BoxCollider>();

        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
            audioSource = gameObject.AddComponent<AudioSource>();

        // Only initialize availableLetters for Letter Lock chests
        if (lockType == "Letter" && (availableLetters == null || availableLetters.Length == 0))
        {
            availableLetters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray();
            Debug.LogWarning("availableLetters not set in Inspector for Letter Lock chest. Defaulting to A-Z.");
        }

        // If availableLetters is used, set the default value for each letter
        if (lockType == "Letter" && availableLetters != null && availableLetters.Length > 0)
        {
            for (int i = 0; i < letters.Length; i++)
            {
                letters[i] = availableLetters[0];
            }
        }
    }

    public void OpenChest()
    {
        if (lockType == "Number")
        {
            OpenLockUI(lockScreenUI);
        }
        else if (lockType == "Key" && EquipSystem.Instance.selectedItem?.name == "Key(Clone)")
        {
            UnlockChest();
        }
        else if (lockType == "Letter")
        {
            OpenLockUI(lockScreenUI2);
        }
    }

    private void OpenLockUI(GameObject lockUI)
    {
        if (!isOpen)
        {
            lockUI.SetActive(true);
            LockPlayerInput();
            ActivateLockUI();
        }
    }

    private void CloseLockUI()
    {
        lockScreenUI.SetActive(false);
        lockScreenUI2.SetActive(false);
        UnlockPlayerInput();
    }

    private void ActivateLockUI()
    {
        if (lockType == "Number")
        {
            RemoveButtonListeners(increaseNumButtons, decreaseNumButtons, checkCodeButton, closeLockUIButton);

            for (int i = 0; i < increaseNumButtons.Length; i++)
            {
                int index = i;
                increaseNumButtons[i].onClick.AddListener(() => IncreaseDigit(index));
                decreaseNumButtons[i].onClick.AddListener(() => DecreaseDigit(index));
            }

            checkCodeButton.onClick.AddListener(CheckCode);
            closeLockUIButton.onClick.AddListener(CloseLockUI);
        }
        else if (lockType == "Letter")
        {
            RemoveButtonListeners(increaseLetterButtons, decreaseLetterButtons, checkCodeButton2, closeLockUIButton2);

            for (int i = 0; i < increaseLetterButtons.Length; i++)
            {
                int index = i;
                increaseLetterButtons[i].onClick.AddListener(() => IncreaseLetter(index));
                decreaseLetterButtons[i].onClick.AddListener(() => DecreaseLetter(index));
            }

            checkCodeButton2.onClick.AddListener(CheckCode);
            closeLockUIButton2.onClick.AddListener(CloseLockUI);
        }
    }

    private void RemoveButtonListeners(Button[] increaseButtons, Button[] decreaseButtons, Button checkButton, Button closeButton)
    {
        foreach (Button btn in increaseButtons) btn.onClick.RemoveAllListeners();
        foreach (Button btn in decreaseButtons) btn.onClick.RemoveAllListeners();
        checkButton.onClick.RemoveAllListeners();
        closeButton.onClick.RemoveAllListeners();
    }

    public void IncreaseDigit(int index)
    {
        digits[index] = (digits[index] + 1) % 10;
        UpdateDisplay();
    }

    public void DecreaseDigit(int index)
    {
        digits[index] = (digits[index] - 1 + 10) % 10;
        UpdateDisplay();
    }

    public void IncreaseLetter(int index)
    {
        if (lockType == "Letter")
        {
            int currentPos = System.Array.IndexOf(availableLetters, letters[index]);
            letters[index] = availableLetters[(currentPos + 1) % availableLetters.Length];
            UpdateDisplay();
        }
    }

    public void DecreaseLetter(int index)
    {
        if (lockType == "Letter")
        {
            int currentPos = System.Array.IndexOf(availableLetters, letters[index]);
            letters[index] = availableLetters[(currentPos - 1 + availableLetters.Length) % availableLetters.Length];
            UpdateDisplay();
        }
    }

    private void UpdateDisplay()
    {
        if (lockType == "Number")
        {
            for (int i = 0; i < digitTexts.Length; i++)
            {
                digitTexts[i].text = digits[i].ToString();
            }
        }
        else if (lockType == "Letter")
        {
            for (int i = 0; i < letterTexts.Length; i++)
            {
                letterTexts[i].text = letters[i].ToString();
            }
        }
    }

    public void CheckCode()
    {
        if (lockType == "Number")
        {
            string enteredCode = string.Join("", digits);
            if (enteredCode == correctCode)
            {
                UnlockChest();
            }
            else
            {
                Debug.Log("Incorrect Code! Try Again.");
            }
        }
        else if (lockType == "Letter")
        {
            string enteredWord = new string(letters);
            if (enteredWord == correctWord)
            {
                UnlockChest();
            }
            else
            {
                Debug.Log("Incorrect Word! Try Again.");
            }
        }
    }

    private void UnlockChest()
    {
        if (!isOpen)
        {
            isOpen = true;

            lockScreenUI.SetActive(false);
            lockScreenUI2.SetActive(false);
            UnlockPlayerInput();

            if (chestOpenSound != null && AudioManager.Instance != null)
            {
                audioSource.volume = AudioManager.Instance.sfxVolume;
                audioSource.PlayOneShot(chestOpenSound);
            }

            // Track chest as unlocked
            if (!string.IsNullOrEmpty(ChestName) && ChestProgressTracker.Instance != null)
            {
                ChestProgressTracker.Instance.UnlockChest(ChestName);
            }

            StartCoroutine(PlayUnlockAnimationWithDelay());
        }
    }

    private IEnumerator PlayUnlockAnimationWithDelay()
    {
        yield return new WaitForSeconds(1.2f);
        animator.SetTrigger("Unlock");
        chestCollider.enabled = false;
    }

    private void LockPlayerInput()
    {
        MouseMovement.OpenLockUI();
        SelectionManager.Instance.DisableSelection();
        SelectionManager.Instance.enabled = false;
    }

    private void UnlockPlayerInput()
    {
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
        MouseMovement.CloseLockUI();
        SelectionManager.Instance.enabled = true;
        SelectionManager.Instance.EnableSelection();
    }
}
