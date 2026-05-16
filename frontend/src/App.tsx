import { useState } from 'react'
import { AppMenu } from './components/AppMenu'
import { MainWindow } from './components/MainWindow'
import { SettingsModal } from './components/modals/SettingsModal'
import { AboutModal } from './components/modals/AboutModal'
import { PortAlert } from './components/modals/PortAlert'
import { useSerialApp } from './hooks/useSerialApp'
import './App.css'

function App() {
  const app = useSerialApp()
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [aboutOpen, setAboutOpen] = useState(false)

  const handleExit = () => {
    if (window.confirm('Завершить работу программы?')) {
      void app.closePhysical()
      window.close()
    }
  }

  return (
    <div className="app-shell">
      <div className="titlebar">Локальная безадаптерная сеть</div>

      <AppMenu
        connected={app.connection === 'connected'}
        portOpen={app.portOpen}
        busy={app.busy}
        onExit={handleExit}
        onOpenPhysical={app.openPhysical}
        onClosePhysical={app.closePhysical}
        onConnect={app.connectLink}
        onDisconnect={app.disconnectLink}
        onSettings={() => setSettingsOpen(true)}
        onAbout={() => setAboutOpen(true)}
      />

      <MainWindow
        settings={app.settings}
        destination={app.destination}
        onDestinationChange={app.setDestination}
        connection={app.connection}
        portOpen={app.portOpen}
        busy={app.busy}
        logs={app.logs}
        onSendMessage={app.sendMessage}
        onOpenPhysical={app.openPhysical}
        onClosePhysical={app.closePhysical}
        onConnect={app.connectLink}
        onDisconnect={app.disconnectLink}
        onSettings={() => setSettingsOpen(true)}
        onExit={handleExit}
      />

      <SettingsModal
        open={settingsOpen}
        settings={app.settings}
        ports={app.ports}
        onChange={app.setSettings}
        onClose={() => setSettingsOpen(false)}
        onApply={async () => {
          setSettingsOpen(false)
          await app.saveSettings()
        }}
      />

      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />

      <PortAlert
        open={app.portOpenedAlert}
        settings={app.settings}
        onClose={() => app.setPortOpenedAlert(false)}
      />
    </div>
  )
}

export default App
