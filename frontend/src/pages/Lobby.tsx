import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { LogOut, MessageSquare, Search, Plus, Users } from "lucide-react";
import { toast } from "sonner";
import { apiUrl } from "@/lib/socket";

interface Room {
  name: string;
  description?: string;
  created_at?: string;
  members?: number;
}

const Lobby = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [rooms, setRooms] = useState<Room[]>([]);
  const [newRoomName, setNewRoomName] = useState("");
  const [description, setDescription] = useState("");
  const [roomType, setRoomType] = useState("text");
  const [pin, setPin] = useState("");
  const [maxFileMb, setMaxFileMb] = useState("");
  const [loading, setLoading] = useState(false);

  const [isAdmin, setIsAdmin] = useState(false);
  const filteredRooms = rooms.filter((room) =>
    (room.name || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleLogout = () => {
    toast.success("Logged out successfully");
    navigate("/login");
  };

  const fetchRooms = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/rooms`);
      const data = await res.json();
      setRooms(data.rooms || []);
    } catch (e) {
      toast.error("Error fetching rooms");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  useEffect(() => {
    setIsAdmin(localStorage.getItem("is_admin") === "true");
    fetchRooms();
  }, []);

  const handleCreateRoom = async () => {
    const name = newRoomName.trim();
    if (!name) return toast.error("Nombre de sala requerido");
    if (roomType !== "text" && roomType !== "multimedia") return toast.error("Tipo de sala inválido");
    try {
      const token = localStorage.getItem("chat_token");
      const body = {
        name,
        description,
        type: roomType,
        pin: pin || undefined,
        max_file_mb: maxFileMb ? parseInt(maxFileMb) : undefined,
      };
      const res = await fetch(`${apiUrl}/rooms`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        return toast.error(data.msg || "Error creando sala");
      }
      toast.success("Sala creada");
      setNewRoomName("");
      setDescription("");
      setRoomType("text");
      setPin("");
      setMaxFileMb("");
      fetchRooms();
    } catch (e) {
      toast.error("Error creando sala");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-card rounded-xl border border-primary/30">
              <MessageSquare className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-primary">AquaChat</h1>
          </div>
          <Button 
            variant="outline" 
            onClick={handleLogout}
            className="border-border hover:border-primary transition-colors"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold text-primary">Salas</h2>
            
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <Input
              type="text"
              placeholder="Buscar salas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-card border-input focus:border-primary"
            />
          </div>

          {isAdmin && (
            <div className="max-w-xl mx-auto my-6 p-6 rounded-xl border border-border bg-card shadow">
              <h3 className="text-lg font-semibold mb-4 text-primary">Crear nueva sala</h3>
              <form
                onSubmit={e => { e.preventDefault(); handleCreateRoom(); }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Nombre</label>
                  <Input
                    placeholder="Nombre de la sala"
                    value={newRoomName}
                    onChange={e => setNewRoomName(e.target.value)}
                    className="bg-card border-input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Descripción</label>
                  <Input
                    placeholder="Descripción "
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    className="bg-card border-input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Tipo de sala</label>
                  <select
                    value={roomType}
                    onChange={e => setRoomType(e.target.value)}
                    className="w-full p-2 rounded border border-input bg-card text-foreground"
                  >
                    <option value="text">Solo texto</option>
                    <option value="multimedia">Multimedia</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">PIN ( mínimo 4 dígitos)</label>
                  <Input
                    placeholder="PIN de la sala"
                    value={pin}
                    onChange={e => setPin(e.target.value)}
                    className="bg-card border-input"
                    maxLength={6}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-foreground">Límite de archivo (MB, opcional) el maximo estandar es de 10MB</label>
                  <Input
                    type="number"
                    placeholder="Máximo tamaño de archivo"
                    value={maxFileMb}
                    onChange={e => setMaxFileMb(e.target.value)}
                    className="bg-card border-input"
                    min={1}
                    max={100}
                    
                  />
                </div>
                <Button type="submit" className="w-full glow-button bg-primary hover:bg-accent text-primary-foreground">
                  Crear sala
                </Button>
              </form>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {filteredRooms.map((room) => (
              <Card
                key={room.name}
                onClick={() => navigate(`/sala/${encodeURIComponent(room.name)}`)}
                className="p-6 bg-card border-border hover:border-primary/50 transition-all cursor-pointer hover:scale-[1.02] duration-300"
              >
                <div className="space-y-3">
                  <h3 className="text-xl font-semibold text-foreground">{room.name}</h3>
                  <p className="text-muted-foreground text-sm">{room.description}</p>
                  <div className="flex items-center gap-2 text-primary">
                    <Users className="w-4 h-4" />
                    <span className="text-sm font-medium">{room.members ?? 0} Participantes</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {filteredRooms.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No hay salas</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Lobby;
