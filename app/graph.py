from typing import TypedDict
from pathlib import Path
from .agents.developer import DeveloperAgent
from .agents.tester import TesterAgent
from .services.git_service import GitService
from .services.events import bus
from .database import SessionLocal, Project, Run, TestRun, Checkpoint
from .config import settings
from langgraph.graph import StateGraph, START, END

class ProjectState(TypedDict, total=False):
    project_id:int; user_request:str; current_task:str; changed_files:list[str]; test_results:dict; current_iteration:int; status:str; errors:list[str]; branch:str; demo_url:str|None

def build_workflow():
    """Compile the explicit Supervisor → Developer → Tester routing graph.

    The runtime persists at every node boundary in ``execute_run``; this compact
    graph remains inspectable/testable and is the orchestration contract for a
    future durable LangGraph checkpointer.
    """
    graph=StateGraph(ProjectState)
    graph.add_node('supervisor',lambda s:{'status':'planned','current_task':s['user_request']})
    graph.add_node('developer',lambda s:{'status':'developing'})
    graph.add_node('tester',lambda s:{'status':'testing'})
    graph.add_node('checkpoint',lambda s:{'status':'completed'})
    graph.add_edge(START,'supervisor'); graph.add_edge('supervisor','developer'); graph.add_edge('developer','tester')
    graph.add_conditional_edges('tester',lambda s:'checkpoint' if s.get('test_results',{}).get('status')=='PASS' else 'developer',{'checkpoint':'checkpoint','developer':'developer'})
    graph.add_edge('checkpoint',END)
    return graph.compile()

async def execute_run(project_id:int, request:str)->None:
    db=SessionLocal(); project=db.get(Project,project_id)
    if not project: db.close(); return
    run=Run(project_id=project_id,request=request,status='running'); db.add(run); project.status='running'; project.current_task=request; db.commit(); db.refresh(run)
    workspace=Path(project.workspace_path); state:ProjectState={'project_id':project_id,'user_request':request,'branch':project.branch,'current_iteration':0,'status':'running'}
    await bus.emit(project_id,'Supervisor','agent_started','Requirement accepted; inspecting existing workspace.',run.id)
    await bus.emit(project_id,'Supervisor','plan_created','Plan: inspect → implement incrementally → execute tests → checkpoint → demo.',run.id)
    developer=DeveloperAgent(); tester=TesterAgent(); results=None
    for iteration in range(1,settings.max_iterations+1):
        state['current_iteration']=iteration
        await bus.emit(project_id,'Developer','agent_started',f'Iteration {iteration}: inspecting and implementing.',run.id)
        try:
            changed=developer.implement(workspace,request,incremental=iteration>1)
            state['changed_files']=changed
            await bus.emit(project_id,'Developer','file_modified',f'Changed {len(changed)} file(s): '+(', '.join(changed) if changed else 'no-op'),run.id)
            await bus.emit(project_id,'Tester','test_started','Running isolated executable test suite.',run.id)
            results=tester.test(workspace); state['test_results']=results
        except Exception as exc:
            results={'status':'FAIL','total':0,'passed':0,'output':str(exc)}; state.setdefault('errors',[]).append(str(exc))
        db.add(TestRun(project_id=project_id,run_id=run.id,status=results['status'],total=results['total'],passed=results['passed'],output=results['output']))
        db.commit()
        await bus.emit(project_id,'Tester','test_finished',f"{results['status']}: {results['passed']}/{results['total']} tests passed.",run.id)
        if results['status']=='PASS': break
        await bus.emit(project_id,'Supervisor','feedback','Tests failed; sending structured output back to Developer.',run.id)
    if results and results['status']=='PASS':
        await bus.emit(project_id,'Git','checkpoint_started','Tests are green; creating validated local checkpoint.',run.id)
        commit,pushed,_=GitService().checkpoint(workspace,project.branch,request)
        cp=Checkpoint(project_id=project_id,description=request,status='PASS',test_count=results['total'],passed_tests=results['passed'],commit_hash=commit,branch=project.branch,pushed=pushed); db.add(cp)
        project.status='completed'; project.demo_url=f'http://127.0.0.1:8001'; run.status='completed'; run.summary=f"Validated CP-{cp.id or 'new'}; launch generated demo with uvicorn backend.main:app --port 8001"
        db.commit(); db.refresh(cp)
        await bus.emit(project_id,'Git','checkpoint_created',f'CP-{cp.id} validated. Commit: {commit or "working tree unchanged"}.',run.id)
        await bus.emit(project_id,'Supervisor','demo_ready',f'Demo ready at {project.demo_url}; run `uvicorn backend.main:app --port 8001` from the generated workspace.',run.id)
    else:
        project.status='failed'; run.status='failed'; run.summary='Retry limit reached; no checkpoint or push was created.'; db.commit()
        await bus.emit(project_id,'Supervisor','error','Retry limit reached. No checkpoint was created.',run.id)
    db.close()
