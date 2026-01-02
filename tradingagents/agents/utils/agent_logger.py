"""Agent Logger - Export prompts and LLM responses for study"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class AgentLogger:
    """Logs agent interactions (prompts, responses, decisions) to files for study."""
    
    def __init__(self, enabled: bool = True, log_dir: Optional[str] = None):
        """
        Initialize the agent logger.
        
        Args:
            enabled: Whether logging is enabled
            log_dir: Directory to save logs. Defaults to ./agent_logs
        """
        self.enabled = enabled
        
        if log_dir is None:
            # Default to project root/agent_logs
            project_root = Path(__file__).parent.parent.parent.parent
            self.log_dir = project_root / "agent_logs"
        else:
            self.log_dir = Path(log_dir)
        
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
        # Track current run
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.log_dir / self.run_id
        
        if self.enabled:
            self.run_dir.mkdir(parents=True, exist_ok=True)
            
        self.interaction_count = 0
    
    def log_agent_interaction(
        self,
        agent_name: str,
        system_prompt: str,
        input_messages: List[Dict[str, Any]],
        llm_response: Any,
        tool_calls: Optional[List[Dict]] = None,
        final_output: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a single agent interaction.
        
        Args:
            agent_name: Name of the agent (e.g., "news_analyst", "trader")
            system_prompt: The system prompt sent to the LLM
            input_messages: List of messages sent as input
            llm_response: The raw LLM response object
            tool_calls: List of tool calls made by the agent
            final_output: The final processed output/report
            metadata: Additional metadata (ticker, date, etc.)
        """
        if not self.enabled:
            return
        
        self.interaction_count += 1
        timestamp = datetime.now().isoformat()
        
        # Extract response content safely
        response_content = self._extract_content(llm_response)
        
        # Ensure system_prompt is a string (handle accidental tuples)
        if isinstance(system_prompt, tuple):
            system_prompt = " ".join(str(s) for s in system_prompt)
        system_prompt = str(system_prompt)
        
        # Build the log entry
        log_entry = {
            "run_id": self.run_id,
            "interaction_id": self.interaction_count,
            "timestamp": timestamp,
            "agent_name": agent_name,
            "system_prompt": system_prompt,
            "input_messages": self._sanitize_messages(input_messages),
            "llm_response": {
                "content": response_content,
                "raw_type": str(type(llm_response)),
            },
            "tool_calls": tool_calls or [],
            "final_output": final_output,
            "metadata": metadata or {}
        }
        
        # Save to individual file
        filename = f"{self.interaction_count:03d}_{agent_name}_{timestamp.replace(':', '-')}.json"
        filepath = self.run_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        # Also save a markdown version for easy reading
        md_filepath = self.run_dir / filename.replace('.json', '.md')
        self._save_markdown(log_entry, md_filepath)
        
        # Update summary file
        self._update_summary(log_entry)
    
    def _extract_content(self, response: Any) -> Any:
        """Extract content from LLM response safely."""
        if hasattr(response, 'content'):
            content = response.content
            # Handle list content (Gemini)
            if isinstance(content, list):
                return [
                    block.get("text", str(block)) if isinstance(block, dict) else str(block)
                    for block in content
                ]
            return str(content)
        return str(response)
    
    def _sanitize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize messages for JSON serialization."""
        sanitized = []
        for msg in messages:
            if isinstance(msg, dict):
                sanitized.append({
                    "role": msg.get("role", "unknown"),
                    "content": str(msg.get("content", ""))[:5000]  # Limit length
                })
            else:
                # Handle AIMessage, HumanMessage, etc.
                try:
                    sanitized.append({
                        "role": getattr(msg, "type", "unknown"),
                        "content": str(getattr(msg, "content", msg))[:5000]
                    })
                except:
                    sanitized.append({"role": "unknown", "content": str(msg)[:5000]})
        return sanitized
    
    def _save_markdown(self, log_entry: Dict[str, Any], filepath: Path):
        """Save a human-readable markdown version of the log."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {log_entry['agent_name']} - Interaction {log_entry['interaction_id']}\n\n")
            f.write(f"**Timestamp:** {log_entry['timestamp']}\n\n")
            
            # Metadata
            if log_entry['metadata']:
                f.write("## Metadata\n\n")
                for key, value in log_entry['metadata'].items():
                    f.write(f"- **{key}:** {value}\n")
                f.write("\n")
            
            # System Prompt
            f.write("## System Prompt\n\n")
            f.write("```\n")
            f.write(log_entry['system_prompt'])
            f.write("\n```\n\n")
            
            # Input Messages
            f.write("## Input Messages\n\n")
            for i, msg in enumerate(log_entry['input_messages'], 1):
                f.write(f"### Message {i} ({msg['role']})\n\n")
                f.write("```\n")
                f.write(msg['content'])
                f.write("\n```\n\n")
            
            # Tool Calls
            if log_entry['tool_calls']:
                f.write("## Tool Calls\n\n")
                for i, tool_call in enumerate(log_entry['tool_calls'], 1):
                    f.write(f"### Tool Call {i}\n\n")
                    f.write(f"**Function:** {tool_call.get('name', 'unknown')}\n\n")
                    f.write("**Arguments:**\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(tool_call.get('args', {}), indent=2))
                    f.write("\n```\n\n")
            
            # LLM Response
            f.write("## LLM Response\n\n")
            f.write("```\n")
            content = log_entry['llm_response']['content']
            if isinstance(content, list):
                f.write("".join(content))
            else:
                f.write(str(content))
            f.write("\n```\n\n")
            
            # Final Output
            if log_entry['final_output']:
                f.write("## Final Output / Report\n\n")
                f.write(log_entry['final_output'])
                f.write("\n\n")
    
    def _update_summary(self, log_entry: Dict[str, Any]):
        """Update the run summary file."""
        summary_file = self.run_dir / "00_SUMMARY.md"
        
        mode = 'a' if summary_file.exists() else 'w'
        
        with open(summary_file, mode, encoding='utf-8') as f:
            if mode == 'w':
                f.write(f"# Agent Interactions Log - Run {self.run_id}\n\n")
                f.write(f"**Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
            
            f.write(f"## {log_entry['interaction_id']}. {log_entry['agent_name']}\n\n")
            f.write(f"- **Time:** {log_entry['timestamp']}\n")
            
            if log_entry['metadata']:
                for key, value in log_entry['metadata'].items():
                    f.write(f"- **{key}:** {value}\n")
            
            f.write(f"- **Tool Calls:** {len(log_entry['tool_calls'])}\n")
            f.write(f"- **Has Output:** {'Yes' if log_entry['final_output'] else 'No'}\n")
            f.write("\n")
    
    def get_log_directory(self) -> str:
        """Get the current run's log directory path."""
        return str(self.run_dir)
    
    def create_index(self):
        """Create an index.html file for easy browsing of logs."""
        if not self.enabled:
            return
        
        index_file = self.run_dir / "index.html"
        
        # Get all json files
        json_files = sorted(self.run_dir.glob("*.json"))
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Agent Logs - {run_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .interaction {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .agent-name {{ font-weight: bold; color: #0066cc; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>Agent Interactions Log</h1>
    <p><strong>Run ID:</strong> {run_id}</p>
    <p><strong>Total Interactions:</strong> {count}</p>
    <hr>
""".format(run_id=self.run_id, count=len(json_files))
        
        for json_file in json_files:
            if json_file.stem == "00_SUMMARY":
                continue
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            md_file = json_file.with_suffix('.md')
            
            html += f"""
    <div class="interaction">
        <div class="agent-name">{data['interaction_id']}. {data['agent_name']}</div>
        <div class="timestamp">{data['timestamp']}</div>
        <div>
            <a href="{md_file.name}">View Markdown</a> | 
            <a href="{json_file.name}">View JSON</a>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html)


# Global logger instance
_global_logger: Optional[AgentLogger] = None


def init_agent_logger(enabled: bool = True, log_dir: Optional[str] = None) -> AgentLogger:
    """Initialize the global agent logger."""
    global _global_logger
    _global_logger = AgentLogger(enabled=enabled, log_dir=log_dir)
    return _global_logger


def get_agent_logger() -> Optional[AgentLogger]:
    """Get the global agent logger instance."""
    return _global_logger


def log_agent_interaction(*args, **kwargs):
    """Convenience function to log using the global logger."""
    if _global_logger:
        _global_logger.log_agent_interaction(*args, **kwargs)

