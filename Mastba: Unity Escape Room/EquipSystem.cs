using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class EquipSystem : MonoBehaviour
{
    public static EquipSystem Instance { get; private set; }

    // UI elements
    public GameObject quickSlotsPanel;
    public List<GameObject> quickSlotsList = new List<GameObject>();
    public GameObject numbersHolder;

    // Current selection
    public int selectedNumber = -1;
    public GameObject selectedItem;

    // Model for the equipped item
    public GameObject toolHolder;
    public GameObject selectedItemModel;

    private void Awake()
    {
        // Singleton pattern to ensure only one instance
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
        }
        else
        {
            Instance = this;
        }
    }

    private void Start()
    {
        PopulateSlotList();
    }

    void Update()
    {
        // Select a quick slot based on key press
        if (Input.GetKeyDown(KeyCode.Alpha1)) SelectQuickSlot(1);
        else if (Input.GetKeyDown(KeyCode.Alpha2)) SelectQuickSlot(2);
        else if (Input.GetKeyDown(KeyCode.Alpha3)) SelectQuickSlot(3);
        else if (Input.GetKeyDown(KeyCode.Alpha4)) SelectQuickSlot(4);
        else if (Input.GetKeyDown(KeyCode.Alpha5)) SelectQuickSlot(5);
        else if (Input.GetKeyDown(KeyCode.Alpha6)) SelectQuickSlot(6);
        else if (Input.GetKeyDown(KeyCode.Alpha7)) SelectQuickSlot(7);
    }

    // Selects the quick slot and equips the item
    void SelectQuickSlot(int number)
    {
        if (checkIfSlotIsFull(number))
        {
            if (selectedNumber != number)
            {
                // Unselect previous item
                if (selectedItem != null)
                    selectedItem.GetComponent<InventoryItem>().isSelected = false;

                selectedNumber = number;
                selectedItem = getSelectedItem(number);
                selectedItem.GetComponent<InventoryItem>().isSelected = true;

                SetEquippedModel(selectedItem);
                UpdateSlotUI(number);
            }
            else
            {
                ClearSelection();
            }
        }
    }

    // Set the model of the selected item
    private void SetEquippedModel(GameObject selectedItem)
    {
        if (selectedItemModel != null)
        {
            DestroyImmediate(selectedItemModel.gameObject);
            selectedItemModel = null;
        }

        string itemName = selectedItem.name.Replace("(Clone)", "");
        Debug.Log(itemName);

        // Instantiate and set the item model at a specific position and rotation
        if (itemName.Contains("Clue"))
        {
            selectedItemModel = Instantiate(Resources.Load<GameObject>(itemName + "_Model"),
                new Vector3(0f, 1.3f, 1.3f), Quaternion.Euler(0, -90f, 0f));
        }
        else if (itemName.Contains("Key"))
        {
            selectedItemModel = Instantiate(Resources.Load<GameObject>(itemName + "_Model"),
                new Vector3(0.5f, 1.3f, 1.3f), Quaternion.Euler(0f, -25f, -90f));
        }

        selectedItemModel.transform.SetParent(toolHolder.transform, false);
    }

    // Get the item from the selected quick slot
    GameObject getSelectedItem(int slotNumber)
    {
        return quickSlotsList[slotNumber - 1].transform.GetChild(0).gameObject;
    }

    // Check if the quick slot is occupied
    bool checkIfSlotIsFull(int slotNumber)
    {
        return quickSlotsList[slotNumber - 1].transform.childCount > 0;
    }

    // Populate the list of quick slots
    private void PopulateSlotList()
    {
        foreach (Transform child in quickSlotsPanel.transform)
        {
            if (child.CompareTag("QuickSlot"))
            {
                quickSlotsList.Add(child.gameObject);
            }
        }
    }

    // Add an item to the quick slots
    public void AddToQuickSlots(GameObject itemToEquip)
    {
        GameObject availableSlot = FindNextEmptySlot();
        itemToEquip.transform.SetParent(availableSlot.transform, false);

        InventorySystem.Instance.ReCalculateList();
    }

    // Find the next available (empty) quick slot
    private GameObject FindNextEmptySlot()
    {
        foreach (GameObject slot in quickSlotsList)
        {
            if (slot.transform.childCount == 0)
            {
                return slot;
            }
        }
        return new GameObject();
    }

    // Check if all quick slots are full
    public bool CheckIfFull()
    {
        int counter = 0;

        foreach (GameObject slot in quickSlotsList)
        {
            if (slot.transform.childCount > 0)
            {
                counter++;
            }
        }

        return counter == 7;
    }

    // Update the UI to reflect the selected slot
    private void UpdateSlotUI(int number)
    {
        foreach (Transform child in numbersHolder.transform)
        {
            child.GetChild(0).transform.GetComponent<TMP_Text>().color = Color.gray;
        }

        TMP_Text toBeChanged = numbersHolder.transform.Find("number" + number).transform.GetChild(0).transform.GetComponent<TMP_Text>();
        toBeChanged.color = Color.white;
    }

    // Clear the selection and reset the UI
    private void ClearSelection()
    {
        selectedNumber = -1;

        if (selectedItem != null)
        {
            selectedItem.GetComponent<InventoryItem>().isSelected = false;
            selectedItem = null;
        }

        if (selectedItemModel != null)
        {
            DestroyImmediate(selectedItemModel.gameObject);
            selectedItemModel = null;
        }

        foreach (Transform child in numbersHolder.transform)
        {
            child.GetChild(0).transform.GetComponent<TMP_Text>().color = Color.gray;
        }
    }
}

