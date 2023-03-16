import Head from 'next/head';
import styles from '@/styles/Home.module.css';
// note that while you can import individual styles like this, global.css will always be applied.
import {useState} from "react";
// Needed to store stateful information.

function renderLateEntryTable(entries, triggerRefreshFunction) {
    function deleteEntry(entry_id) {
        const [day, month, year] = entry_id.split("/")
        fetch(
            `/api/lates/${year}/${month}/${day}`,
            {
                method: "DELETE"
            }
        ).then((response)=>{response.ok ? triggerRefreshFunction() : null})
    }

    return (
      <table className={styles.mainTable}>
        <thead>
            <tr>
                <th title={"dd/mm/yyyy"}>Date</th>
                {/* title={"..."} just shows a tooltip when the text is hovered over. Semantics. */}
                <th>Minutes Late</th>
                <th>Excuse</th>
            </tr>
        </thead>
          <tbody>
              {
                  // Now for the fun part - dynamically rendering!
                  // Here we will map entries (an object of {date: {key: value}}) into a table row per entry.
                  Object.keys(entries).map(
                      (key, _id) => {
                          // _id is required so that nextJS builds the page properly
                          // I'm not entirely sure why but don't question it.
                          let entry = entries[key];
                          return (
                              <tr key={_id}>
                                  <td>{key}</td>
                                  <td>{entry.minutes_late}</td>
                                  <td>{entry.excuse || "No excuse"}</td>
                                  <td>
                                      <button onClick={()=>{deleteEntry(key)}}>
                                          delete
                                      </button>
                                  </td>
                              </tr>
                          )
                      }
                  )
              }
          </tbody>
      </table>
    )
  // This function will return a full HTML table, like below:
  /*

    <table>
      <tr>
        <th title="dd/mm/YY">Date</th>
        <th>Minutes Late</th>
        <th>Excuse</th>
      </tr>
      <tr>
        <td>1/1/2023</td>
        <td>15</td>
        <td>No excuse</td>
      </tr>
    </table

   */
}


function ShowAllEntries() {
  const [entries, setEntries] = useState(null);
  // We need the above in order to load the data.
  // When we're called, we still need to render something.
  // When setEntries() is called, the component will update.
  if(entries===null) {
    fetch("/api/lates/all")
    .then(
        (response) => response.json().then((data)=>{setEntries(data)})
    )
    return <p>Loading...</p>
  }
  else {
    return renderLateEntryTable(entries, () => {setEntries(null)});
  }
}

function CreateNewEntry() {
  const [created, setCreated] = useState(null);
  function sendForm(event) {
    event.preventDefault();
    // let form_data = {
    //   minutes_late: event.target[0].value,
    //   excuse: event.target[1].value || null
    // }
    let form_data = new FormData(event.target);
    event.target[2].enabled = false;
    fetch(
        "/api/lates",
        {
            body: form_data,
            method: "POST",
        }
    )
        .catch(
            (e) => {
                console.error(e);
                event.target[2].enabled = true;
            }
        )
        .then(
            (response) => {
                setCreated(response.ok);
                event.target[2].enabled = true;
            }
        )
  }

  let status;
  if(created === null) {
      status = null;
  }
  else if(created === true) {
      status = (
          <div style={{background: "green", padding: "2rem"}}>
              <p>Entry created!</p>
          </div>
      )
  }
  else {
      status = (
          <div style={{background: "red", padding: "2rem"}}>
              <p>Failed</p>
          </div>
      )
  }

  return (
      <>
          {status}
          <form onSubmit={sendForm}>
            <label htmlFor={"minutes_late"}>Minutes late </label>
            <input type={"number"} min={0} max={32400} id={"minutes_late"} name={"minutes_late"} required={true}/>
            <br/>
            <label htmlFor={"excuse"}>Excuse </label>
            <input type={"text"} maxLength={1024} id={"excuse"} name={"excuse"}/>
            <br/>
            <input type={"submit"}/>
          </form>
      </>
  )
}

export default function Home() {
  const [view, setView] = useState(null);
  // here, we get two things:
  // * View: currently null, possibly a string. The currently viewed pane.
  // * setView: generic function that takes one argument - the new state to set.

  return (
    <>  {/*
        <> and </> allow us to return multiple elements in one return function.
        Think of it as opening and closing an array, just it contains HTML instead.
      */}
      <Head>
        <title>Nex Late Tracker - WebUI</title>
        <meta name="description" content="How late is nex today? We'll see!" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main> {/* className={styles.xyz} is required to use imported stylesheets */}
        <div style={{textAlign: "center"}}>
          <h1>Nex Late Tracker</h1>
          <h2>She&apos;s never on time anyway</h2>
          {/* You can't use characters like ', &, ", <, >, etc, without escaping. */}
        </div>
        <div style={{display: "flex", justifyContent: "space-between", alignContent: "center", margin: "0 auto", width: "25%"}}>
          {/* Action button row */}
          <button onClick={()=>{setView("render_all")}}>
            Load all lates
          </button>
          <button onClick={()=>{setView("create_new")}}>
            Create late entry
          </button>
        </div>
        <hr/>
        <div>
          {
            (
                () => {
                  switch (view) {
                    case "render_all":
                      return <ShowAllEntries/>

                    case "create_new":
                      return <CreateNewEntry/>

                    default:
                      return <p>Current view: {view}</p>
                  }
                }
            )()
          }
        </div>
      </main>
    </>
  )
}
