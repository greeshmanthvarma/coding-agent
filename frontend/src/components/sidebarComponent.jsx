import { Sidebar, SidebarHeader, SidebarContent, SidebarGroup, SidebarGroupLabel, SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from "./ui/sidebar"

export function SidebarComponent() {
  return (
    <Sidebar>
      <SidebarHeader>
        <h2 className="text-2xl text-foreground mb-4 pl-2 pt-4">
          <span className="italic tracking-tightest">Repo</span><span className="font-bold tracking-tightest">Refine</span>  
        </h2>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel><span className="pl-2">Chat History</span></SidebarGroupLabel>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}