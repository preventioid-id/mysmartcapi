import localforage from "localforage";

const interviewDB = localforage.createInstance({
  name: "smartcapi",
  storeName: "interviews",
});

export async function saveInterviewLocally(data) {
  const id = data.id || Date.now().toString();
  await interviewDB.setItem(id, { ...data, synced: false });
}

export async function getPendingSyncData() {
  const all = [];
  await interviewDB.iterate((value) => {
    if (!value.synced) all.push(value);
  });
  return all;
}

export async function markAsSynced(id) {
  const record = await interviewDB.getItem(id);
  if (record) {
    record.synced = true;
    await interviewDB.setItem(id, record);
  }
}
