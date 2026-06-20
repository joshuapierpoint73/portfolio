using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class InteractableObject : MonoBehaviour
{
    public string ItemName;
    public string InteractionMsg;
    public bool playerInRange;
    public GameObject textBox;

    // Retrieves the name of the item
    public string GetItemName()
    {
        return ItemName;
    }

    void Update()
    {
        // Close the text box when the Enter key is pressed
        if (Input.GetKeyDown(KeyCode.Return) && textBox.gameObject.activeSelf)
        {
            textBox.gameObject.SetActive(false);
        }

        // Interact with the object when the mouse is clicked
        if (Input.GetKeyDown(KeyCode.Mouse0) && playerInRange && SelectionManager.Instance.onTarget && SelectionManager.Instance.selectedObject == gameObject)
        {
            HandleInteraction();
        }
    }

    public string GetInteractionMsg()
    {
        return InteractionMsg;
    }

    private void HandleInteraction()
    {
        if (CompareTag("Container"))
        {
            OpenChest();
        }
        else if (CompareTag("PharoahBust"))
        {
            DisplayPharaohBustMessages();
        }
        else if (CompareTag("Sphinx"))
        {
            DisplaySphinxMessages();
        }
        else if (CompareTag("SetHint"))
        {
            DisplaySetHints();
        }
        else if (CompareTag("Harp"))
        {
            HarpPuzzle.Instance.PlayHarp(ItemName);
        }
        else if (CompareTag("CatStatue"))
        {
            CatManager.Instance.RotateStatue(SelectionManager.Instance.selectedObject);
        }
        else
        {
            TryAddToInventory();
        }
    }

    private void OpenChest()
    {
        ChestLockSystem chestLock = GetComponentInChildren<ChestLockSystem>();
        if (chestLock != null)
        {
            chestLock.OpenChest();
        }
    }

    private void DisplayPharaohBustMessages()
    {
        textBox.gameObject.SetActive(true);
        TMP_Text tmpText = textBox.GetComponentInChildren<TMP_Text>();

        switch (ItemName)
        {
            case "PharoahBust1":
                tmpText.text = "Pharaoh A: Pharaoh B is the liar, and the code is Small, Medium, Large.";
                break;
            case "PharoahBust2":
                tmpText.text = "Pharaoh B: The code is Small, Large, Small, Medium.";
                break;
            case "PharoahBust3":
                tmpText.text = "Pharaoh C: Pharaoh B is telling the truth.";
                break;
        }
    }

    private void DisplaySphinxMessages()
    {
        textBox.gameObject.SetActive(true);
        TMP_Text tmpText = textBox.GetComponentInChildren<TMP_Text>();

        switch (ItemName)
        {
            case "Sphinx1":
                tmpText.text = "Sphinx: What can run, but never walks; has a mouth, but never talks; has a head, but never weeps; has a bed, but never sleeps?";
                break;
            case "Sphinx2":
                tmpText.text = "Sphinx: I seem clear but when you look through me, things get warped. I can be used both for better and for worse.";
                break;
        }
    }
    private void DisplaySetHints()
    {
        textBox.SetActive(true);
        TMP_Text tmpText = textBox.GetComponentInChildren<TMP_Text>();

        var unlockedList = ChestProgressTracker.Instance?.GetUnlockedChests();
        if (unlockedList == null || unlockedList.Count == 0)
        {
            tmpText.text = "Set: The key to solve the equation is hiding away";
            GameTimer.Instance.RemoveTimeForHint();
            return;
        }

        HashSet<string> unlocked = new HashSet<string>(unlockedList);

        // Check if a specific chest is missing from the unlocked list
        if (!unlocked.Contains("KeyChest"))
        {
            tmpText.text = "Set: The key to solve the equation is hiding away.";
        }
        else if (!unlocked.Contains("MathChest"))
        {
            tmpText.text = "Set: You must read paper to solve the equation.";
        }
        else if (!unlocked.Contains("Sphinx1Chest"))
        {
            tmpText.text = "Set: The Sphinx told me he wanted to talk to you!";
        }
        else if (!unlocked.Contains("AhnkChest"))
        {
            tmpText.text = "Set: Things must be examined closely to unveil the whole truth.";
        }
        else if (unlocked.SetEquals(new HashSet<string> { "KeyChest", "AhnkChest","Sphinx1Chest","MathChest" }))
        {
            tmpText.text = "Set: Cats on the move. Put together what you have found to cross safely.";

        }
        else if (!unlocked.Contains("Sphinx2Chest"))
        {
            tmpText.text = "Set: A mystical brother awaits you.";
        }
        else if (!unlocked.Contains("TextChest"))
        {
            tmpText.text = "Set: You must r3ad between the l1nes.";
        }
        else if (!unlocked.Contains("SymbolChest"))
        {
            tmpText.text = "Set: On these 4 walls I group up";
        }
        else if (unlocked.SetEquals(new HashSet<string> { "Sphinx2Chest", "TextChest", "SymbolChest" }))
        {
            tmpText.text = "Set: There is a liar in out mist but he enjoys musi.c";

        }
        else
        {
            tmpText.text = "Set: Keep going. Each chest brings you closer to the truth.";
        }

        GameTimer.Instance.RemoveTimeForHint();
    }


    private void TryAddToInventory()
    {
        if (!InventorySystem.Instance.CheckIfFull())
        {
            InventorySystem.Instance.AddToInventory(ItemName);
            Destroy(gameObject);
        }
        else
        {
            Debug.Log("Inventory full");
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            playerInRange = true;
        }
    }

    private void OnTriggerExit(Collider other)
    {
        if (other.CompareTag("Player"))
        {
            playerInRange = false;
        }
    }
}
