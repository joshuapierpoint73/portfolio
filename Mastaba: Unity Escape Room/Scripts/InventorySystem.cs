using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class InventorySystem : MonoBehaviour
{
    public static InventorySystem Instance { get; set; }

    public GameObject inventoryScreenUI;
    public List<GameObject> slotList = new List<GameObject>();
    public List<string> itemList = new List<string>();

    private GameObject itemToAdd;
    private GameObject whatSlotToEquip;
    public bool isOpen;

    // Ensures only one instance of InventorySystem exists
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
        }
        else
        {
            Instance = this;
        }
    }

    void Start()
    {
        isOpen = false;
        PopulateSlotList();
        Cursor.visible = false;
    }

    // Populates the slot list with slots from the UI
    private void PopulateSlotList()
    {
        foreach (Transform child in inventoryScreenUI.transform)
        {
            if (child.CompareTag("Slot"))
            {
                slotList.Add(child.gameObject);
            }
        }
    }

    void Update()
    {
        // Toggle inventory screen with 'E' key
        if (Input.GetKeyDown(KeyCode.E) && !isOpen)
        {
            OpenInventory();
        }
        else if (Input.GetKeyDown(KeyCode.E) && isOpen)
        {
            CloseInventory();
        }
    }

    // Opens the inventory screen and modifies cursor state
    private void OpenInventory()
    {
        Debug.Log("E is pressed");
        inventoryScreenUI.SetActive(true);

        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;

        SelectionManager.Instance.DisableSelection();
        SelectionManager.Instance.GetComponent<SelectionManager>().enabled = false;
        isOpen = true;
    }

    // Closes the inventory screen and restores cursor state
    private void CloseInventory()
    {
        inventoryScreenUI.SetActive(false);

        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;

        SelectionManager.Instance.EnableSelection();
        SelectionManager.Instance.GetComponent<SelectionManager>().enabled = true;
        isOpen = false;
    }

    // Adds an item to the inventory by placing it in the next available slot
    public void AddToInventory(string itemName)
    {
        whatSlotToEquip = FindNextEmptySlot();

        // Instantiate the item and position it correctly in the slot
        itemToAdd = Instantiate(Resources.Load<GameObject>(itemName), whatSlotToEquip.transform.position, whatSlotToEquip.transform.rotation);

        // Parent the item to the slot
        itemToAdd.transform.SetParent(whatSlotToEquip.transform, false);
        itemToAdd.transform.localScale = Vector3.one;
        itemToAdd.transform.localPosition = Vector3.zero;
        itemToAdd.transform.localRotation = Quaternion.identity;

        itemList.Add(itemName);
        ReCalculateList();
    }

    // Checks if the inventory is full
    public bool CheckIfFull()
    {
        int counter = 0;

        foreach (GameObject slot in slotList)
        {
            if (slot.transform.childCount != 0)
            {
                counter += 1;
            }
        }

        return counter == 21;
    }

    // Finds the next empty slot in the inventory
    private GameObject FindNextEmptySlot()
    {
        foreach (GameObject slot in slotList)
        {
            if (slot.transform.childCount == 0)
            {
                return slot;
            }
        }

        return new GameObject();
    }

    // Recalculates the list of items based on the current slots
    public void ReCalculateList()
    {
        itemList.Clear();

        foreach (GameObject slot in slotList)
        {
            if (slot.transform.childCount != 0)
            {
                string name = slot.transform.GetChild(0).name;
                string str2 = "(Clone)";
                string result = name.Replace(str2, "");

                itemList.Add(result);
            }
        }
    }
}
