import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth"; 
import { getDatabase } from "firebase/database";

const firebaseConfig = {
  apiKey: "AIzaSyCwXlPO6UfVSW7N8o-XcAqXGUPUwV2bunI",
  authDomain: "NavNexus-ffafe.firebaseapp.com",
  databaseURL: "https://navnexus-default-rtdb.firebaseio.com/",
  projectId: "NavNexus-ffafe",
  storageBucket: "NavNexus-ffafe.appspot.com",
  messagingSenderId: "106618056802",
  appId: "1:106618056802:web:f0c361438a41eb61d1213b",
  measurementId: "G-QG4MTRJZMJ"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const database = getDatabase(app);
