import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { LogOut, MessageSquare, Search, Plus, Users } from "lucide-react";
import { toast } from "sonner";

interface Room {
  id: string;
  name: string;
  description: string;
  members: number;
}

const mockRooms: Room[] = [
  { id: "1", name: "General Chat", description: "Welcome to the main lobby", members: 42 },
  { id: "2", name: "Tech Talk", description: "Discuss latest in technology", members: 28 },
  { id: "3", name: "Random", description: "Talk about anything", members: 56 },
  { id: "4", name: "Gaming", description: "For gaming enthusiasts", members: 34 },
];

const Lobby = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [rooms] = useState<Room[]>(mockRooms);

  const filteredRooms = rooms.filter(room =>
    room.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleLogout = () => {
    toast.success("Logged out successfully");
    navigate("/login");
  };

  const handleCreateRoom = () => {
    toast.info("Create room feature coming soon!");
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
            <h2 className="text-3xl font-bold text-primary">Lobbies</h2>
            <Button 
              onClick={handleCreateRoom}
              className="glow-button bg-primary hover:bg-accent text-primary-foreground"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Room
            </Button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <Input
              type="text"
              placeholder="Search rooms..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-card border-input focus:border-primary"
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {filteredRooms.map((room) => (
              <Card
                key={room.id}
                onClick={() => navigate(`/sala/${room.id}`)}
                className="p-6 bg-card border-border hover:border-primary/50 transition-all cursor-pointer hover:scale-[1.02] duration-300"
              >
                <div className="space-y-3">
                  <h3 className="text-xl font-semibold text-foreground">{room.name}</h3>
                  <p className="text-muted-foreground text-sm">{room.description}</p>
                  <div className="flex items-center gap-2 text-primary">
                    <Users className="w-4 h-4" />
                    <span className="text-sm font-medium">{room.members} members</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {filteredRooms.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No rooms found</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Lobby;
